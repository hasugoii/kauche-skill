"""KAUCHE catalog via the Shopify Storefront GraphQL API — the app's own path.

The KAUCHE app fetches a Shopify **Storefront access token** at startup (the
`customer/v1/launch` RPC, works anonymously) and then talks to the Storefront
GraphQL API at `https://<shop_domain>/api/2026-04/graphql`. That API is rate-limited
by a **generous per-token cost budget**, not the harsh per-IP anti-bot limit that
guards the public website (`kauche.myshopify.com/search`, `/products/x.json`, ~10
req/min). So going through GraphQL is both the legitimate app path and the way to
avoid 429s.

This module uses GraphQL as the primary path for search / product / collection and
keeps the old anonymous website scraping as a fallback (used only if launch/GraphQL
fails). Checkout stays app-only. See references/internal-api.md + storefront-api.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# Process-wide throttle. Two tiers: the website (web_*) needs wide spacing; the
# GraphQL API (token-based) only needs a light touch + backoff on THROTTLED.
_LOCK = threading.Lock()
_STATE = {"last": 0.0, "cooldown_until": 0.0}


class RateLimited(Exception):
    """Storefront returned 429/THROTTLED past our retries; back off and retry shortly."""


STORE = "https://kauche.myshopify.com"
SHARE_BASE = "https://kauche.com/products/"
UA = "Mobile Buy SDK Android/2026.4.0/com.kauche.kauche"
WEB_UA = "kauche-skill/1.0 (+https://github.com/hasugoii/kauche-skill)"
API_VERSION = "2026-04"
INTERVAL = float(os.environ.get("KAUCHE_INTERVAL", "2.5"))          # website spacing
GQL_INTERVAL = float(os.environ.get("KAUCHE_GQL_INTERVAL", "0.4"))  # GraphQL spacing
CACHE_TTL = int(os.environ.get("KAUCHE_CACHE_TTL", "600"))
CACHE_DIR = os.environ.get("KAUCHE_CACHE_DIR", os.path.join(os.path.expanduser("~"), ".cache", "kauche-api", "shopify"))
TOKEN_CACHE = os.environ.get("KAUCHE_STOREFRONT_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "kauche-api", "storefront.json"))
TOKEN_TTL = int(os.environ.get("KAUCHE_STOREFRONT_TTL", "3600"))


def handle_from(arg: str) -> str:
    m = re.search(r"/products/([^/?#]+)", arg or "")
    return m.group(1) if m else (arg or "").strip()


def share_link(handle: str) -> str:
    return SHARE_BASE + handle


def _num(gid_or_id) -> int | None:
    """Trailing numeric id from a Shopify GID (gid://shopify/Product/123 -> 123)."""
    m = re.search(r"(\d+)\s*$", str(gid_or_id or ""))
    return int(m.group(1)) if m else None


def _money(m) -> str | None:
    """Storefront MoneyV2 amount ('980.0') -> '980' (prices are tax-included yen)."""
    if not m:
        return None
    a = m.get("amount") if isinstance(m, dict) else m
    if a is None:
        return None
    try:
        f = float(a)
        return str(int(f)) if f == int(f) else str(a)
    except (TypeError, ValueError):
        return str(a)


class ShopifyStorefront:
    def __init__(self, interval: float = INTERVAL, cache_ttl: int = CACHE_TTL, api=None):
        self.interval = interval
        self.cache_ttl = cache_ttl
        self._api = api              # a KaucheAPI, to fetch the launch token (lazy)
        self._cfg = None             # cached {shop_domain, storefront_access_token}

    # ---------- Storefront token (via the launch RPC) ----------
    def _config(self) -> dict | None:
        """{'shop_domain','storefront_access_token'} from customer/v1/launch, cached to
        disk (TTL). Returns None if it can't be obtained (callers then fall back to web)."""
        if self._cfg:
            return self._cfg
        try:
            if os.path.exists(TOKEN_CACHE) and time.time() - os.path.getmtime(TOKEN_CACHE) < TOKEN_TTL:
                with open(TOKEN_CACHE, encoding="utf-8") as f:
                    c = json.load(f)
                if c.get("storefront_access_token"):
                    self._cfg = c
                    return c
        except Exception:
            pass
        try:
            if self._api is None:
                from .connect import KaucheAPI
                self._api = KaucheAPI()
            cfg = self._api.storefront_config()
            if cfg.get("storefront_access_token"):
                self._cfg = cfg
                os.makedirs(os.path.dirname(TOKEN_CACHE), exist_ok=True)
                with open(os.open(TOKEN_CACHE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as f:
                    json.dump(cfg, f)
                return cfg
        except Exception:
            pass
        return None

    def _gql(self, query: str, variables: dict, cache_key: str = None) -> dict:
        """One GraphQL POST to the Storefront API. Light throttle + backoff on
        THROTTLED/429. Raises RateLimited after retries. Returns the `data` block."""
        cfg = self._config()
        if not cfg:
            raise RateLimited("no storefront token (launch RPC failed)")
        if cache_key:
            cp = self._cache("gql:" + cache_key)
            if os.path.exists(cp) and time.time() - os.path.getmtime(cp) < self.cache_ttl:
                with open(cp, encoding="utf-8") as f:
                    return json.load(f)
        url = f"https://{cfg['shop_domain']}/api/{API_VERSION}/graphql"
        payload = json.dumps({"query": query, "variables": variables}).encode()
        headers = {
            "Content-Type": "application/json", "Accept": "application/json",
            "X-Shopify-Storefront-Access-Token": cfg["storefront_access_token"],
            "User-Agent": UA, "X-SDK-Version": "2026.4.0",
        }
        with _LOCK:
            for attempt in range(6):
                now = time.time()
                wait = max(_STATE["cooldown_until"] - now, _STATE["last"] + GQL_INTERVAL - now, 0.0)
                if wait:
                    time.sleep(wait + random.uniform(0, 0.2))
                _STATE["last"] = time.time()
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, data=payload, headers=headers), timeout=30) as r:
                        d = json.loads(r.read().decode("utf-8", "replace"))
                except urllib.error.HTTPError as e:
                    if e.code not in (429, 430):
                        raise
                    ra = e.headers.get("Retry-After")
                    _STATE["cooldown_until"] = time.time() + (float(ra) if (ra and ra.isdigit()) else [1, 2, 4, 8, 16][min(attempt, 4)])
                    continue
                except (urllib.error.URLError, TimeoutError):
                    _STATE["cooldown_until"] = time.time() + [1, 2, 4, 8, 16][min(attempt, 4)]
                    continue
                errs = d.get("errors") or []
                if any((e.get("extensions") or {}).get("code") == "THROTTLED" for e in errs):
                    _STATE["cooldown_until"] = time.time() + [1, 2, 4, 8, 16][min(attempt, 4)]
                    continue
                data = d.get("data")
                if data is None and errs:
                    raise ValueError("Storefront GraphQL error: " + json.dumps(errs)[:300])
                if cache_key:
                    os.makedirs(CACHE_DIR, exist_ok=True)
                    with open(cp, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                return data
            raise RateLimited("Storefront GraphQL throttled; try again shortly.")

    # ---------- public API (GraphQL primary, web fallback) ----------
    _SEARCH_Q = """
    query($q:String!,$n:Int!){
      search(query:$q, types:PRODUCT, first:$n){
        edges{ node{ ... on Product {
          id handle title vendor productType availableForSale
          variants(first:1){ edges{ node{ price{amount} compareAtPrice{amount} } } }
          featuredImage{ url }
        } } }
      }
    }"""

    def search(self, query: str, limit: int = 12) -> list:
        """Keyword search via the Storefront GraphQL `search` connection (the app's path;
        token-based quota, no per-IP 429). Returns [{id,handle,title,vendor,price,
        compare_at_price,available,share_link}]; id is the numeric Shopify product id."""
        try:
            data = self._gql(self._SEARCH_Q, {"q": query, "n": limit}, cache_key=f"search:{query}:{limit}")
            out = []
            for e in (data.get("search") or {}).get("edges", []):
                n = e.get("node") or {}
                if not n.get("id"):
                    continue
                v = ((n.get("variants") or {}).get("edges") or [{}])
                vn = (v[0] or {}).get("node") or {}
                price, cmp = _money(vn.get("price")), _money(vn.get("compareAtPrice"))
                out.append({
                    "id": _num(n["id"]), "handle": n.get("handle"), "title": n.get("title"),
                    "vendor": n.get("vendor"), "price": price, "compare_at_price": cmp,
                    "available": n.get("availableForSale"),
                    "image": (n.get("featuredImage") or {}).get("url"),
                    "share_link": share_link(n.get("handle")) if n.get("handle") else None,
                })
            return out
        except RateLimited:
            return self._web_search(query, limit)

    _PRODUCT_Q = """
    query($h:String!){
      product(handle:$h){
        id handle title vendor productType descriptionHtml availableForSale
        featuredImage{ url }
        images(first:10){ edges{ node{ url } } }
        variants(first:30){ edges{ node{ id title price{amount} compareAtPrice{amount} availableForSale sku } } }
      }
    }"""

    def product(self, handle_or_url: str) -> dict:
        h = handle_from(handle_or_url)
        try:
            data = self._gql(self._PRODUCT_Q, {"h": h}, cache_key=f"product:{h}")
            p = data.get("product")
            if not p:
                return self._web_product(h)
            vs = [(e.get("node") or {}) for e in (p.get("variants") or {}).get("edges", [])]
            v0 = vs[0] if vs else {}
            price, cmp = _money(v0.get("price")), _money(v0.get("compareAtPrice"))
            off = None
            try:
                if cmp and float(cmp) > float(price):
                    off = round(100 * (1 - float(price) / float(cmp)))
            except (TypeError, ValueError):
                pass
            return {
                "id": _num(p["id"]), "handle": p.get("handle"), "title": p.get("title"),
                "vendor": p.get("vendor"), "product_type": p.get("productType"),
                "price": price, "compare_at_price": cmp, "discount_pct": off,
                "available": p.get("availableForSale"),
                "image": (p.get("featuredImage") or {}).get("url"),
                "images": [(e.get("node") or {}).get("url") for e in (p.get("images") or {}).get("edges", [])],
                "variants_detail": [
                    {"id": _num(v.get("id")), "title": v.get("title"), "price": _money(v.get("price")),
                     "compare_at_price": _money(v.get("compareAtPrice")), "available": v.get("availableForSale"),
                     "sku": v.get("sku")} for v in vs
                ],
                "body_html": p.get("descriptionHtml"),
                "product_gid": _num(p["id"]),
                "share_link": share_link(p.get("handle")) if p.get("handle") else None,
            }
        except RateLimited:
            return self._web_product(h)

    _COLLECTION_Q = """
    query($h:String!,$n:Int!){
      collection(handle:$h){
        products(first:$n){ edges{ node{
          id handle title vendor productType availableForSale
          variants(first:1){ edges{ node{ price{amount} compareAtPrice{amount} } } }
          featuredImage{ url }
        } } }
      }
    }"""

    def collection_products(self, handle: str, limit: int = 50, page: int = 1):
        try:
            data = self._gql(self._COLLECTION_Q, {"h": handle, "n": limit}, cache_key=f"col:{handle}:{limit}:{page}")
            col = data.get("collection")
            if not col:
                return self._web_collection_products(handle, limit, page)
            out = []
            for e in (col.get("products") or {}).get("edges", []):
                n = e.get("node") or {}
                v = ((n.get("variants") or {}).get("edges") or [{}])
                vn = (v[0] or {}).get("node") or {}
                price, cmp = _money(vn.get("price")), _money(vn.get("compareAtPrice"))
                off = None
                try:
                    if cmp and float(cmp) > float(price):
                        off = round(100 * (1 - float(price) / float(cmp)))
                except (TypeError, ValueError):
                    pass
                out.append({
                    "id": _num(n["id"]), "handle": n.get("handle"), "title": n.get("title"),
                    "vendor": n.get("vendor"), "product_type": n.get("productType"),
                    "price": price, "compare_at_price": cmp, "discount_pct": off,
                    "available": n.get("availableForSale"),
                    "image": (n.get("featuredImage") or {}).get("url"),
                    "share_link": share_link(n.get("handle")) if n.get("handle") else None,
                })
            return out
        except RateLimited:
            return self._web_collection_products(handle, limit, page)

    def collections(self, all_pages: bool = False, max_pages: int = 3):
        """List collections. Uses the website JSON (gives products_count, which the
        Storefront API does not expose). Rarely called; still web-throttled."""
        cols, page = [], 1
        while True:
            d = self.fetch(f"/collections.json?limit=250&page={page}")
            cols += d["collections"]
            if len(d["collections"]) < 250 or not all_pages or page >= max_pages:
                break
            page += 1
        return cols

    # ---------- website fallback (anonymous, harsh per-IP limit) ----------
    def _cache(self, url):
        return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".json")

    def _http(self, url: str, accept: str) -> str:
        headers = {"User-Agent": WEB_UA, "Accept": accept, "Accept-Language": "ja"}
        with _LOCK:
            for attempt in range(6):
                now = time.time()
                wait = max(_STATE["cooldown_until"] - now, _STATE["last"] + self.interval - now, 0.0)
                if wait:
                    time.sleep(wait + random.uniform(0, 0.4))
                _STATE["last"] = time.time()
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                        return r.read().decode("utf-8", "replace")
                except urllib.error.HTTPError as e:
                    if e.code != 429:
                        raise
                    ra = e.headers.get("Retry-After")
                    back = float(ra) if (ra and ra.isdigit()) else [2, 5, 10, 20, 40][min(attempt, 4)]
                    _STATE["cooldown_until"] = time.time() + back
            raise RateLimited("Shopify rate limit; try again in a minute (requests are throttled to recover).")

    def fetch(self, path: str, use_cache: bool = True) -> dict:
        url = path if path.startswith("http") else STORE + path
        cp = self._cache(url)
        if use_cache and os.path.exists(cp) and time.time() - os.path.getmtime(cp) < self.cache_ttl:
            with open(cp, encoding="utf-8") as f:
                return json.load(f)
        data = json.loads(self._http(url, "application/json"))
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return data

    def _web_collection_products(self, handle: str, limit: int = 50, page: int = 1):
        d = self.fetch(f"/collections/{handle}/products.json?limit={limit}&page={page}")
        return [self.summarize(p) for p in d["products"]]

    def _web_product(self, handle_or_url: str) -> dict:
        h = handle_from(handle_or_url)
        p = self.fetch(f"/products/{h}.json")["product"]
        s = self.summarize(p)
        s["body_html"] = p.get("body_html")
        s["variants_detail"] = [
            {"id": v["id"], "title": v["title"], "price": v["price"],
             "compare_at_price": v.get("compare_at_price"), "available": v.get("available"), "sku": v.get("sku")}
            for v in p.get("variants", [])
        ]
        s["images"] = [i["src"] for i in p.get("images", [])]
        s["product_gid"] = p["id"]
        return s

    def _web_search(self, query: str, limit: int = 12) -> list:
        import html as _html
        q = urllib.parse.quote(query)
        url = f"{STORE}/search?q={q}&type=product"
        raw = self._fetch_text(url)
        chunks = raw.split("StandardCardNoMediaLink--")[1:]
        out, seen = [], set()
        for ch in chunks:
            mid = re.match(r"(\d{6,})", ch)
            mh = re.search(r"/products/([0-9a-f-]{36})", ch)
            if not (mid and mh):
                continue
            pid, handle = mid.group(1), mh.group(1)
            if pid in seen:
                continue
            seen.add(pid)
            mt = re.search(r">\s*([^<]{3,})</a>", ch)
            title = _html.unescape(mt.group(1).strip()) if mt else None
            mp = re.search(r"¥([0-9,]+)", ch)
            price = mp.group(1).replace(",", "") if mp else None
            out.append({"id": int(pid), "handle": handle, "title": title, "price": price,
                        "share_link": share_link(handle)})
            if len(out) >= limit:
                break
        return out

    def _fetch_text(self, url: str) -> str:
        cp = self._cache(url) + ".html"
        if os.path.exists(cp) and time.time() - os.path.getmtime(cp) < self.cache_ttl:
            with open(cp, encoding="utf-8", errors="replace") as f:
                return f.read()
        txt = self._http(url, "text/html")
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cp, "w", encoding="utf-8") as f:
            f.write(txt)
        return txt

    @staticmethod
    def summarize(p: dict) -> dict:
        v = (p.get("variants") or [{}])[0]
        price, cmp = v.get("price"), v.get("compare_at_price")
        off = None
        try:
            if cmp and float(cmp) > float(price):
                off = round(100 * (1 - float(price) / float(cmp)))
        except (TypeError, ValueError):
            pass
        tags = p.get("tags") or []

        def tag(k):
            for t in tags:
                if t.startswith(k + ":"):
                    return t.split(":", 1)[1]
            return None
        return {
            "id": p["id"], "handle": p["handle"], "title": p["title"],
            "vendor": p.get("vendor"), "product_type": p.get("product_type"),
            "price": price, "compare_at_price": cmp, "discount_pct": off,
            "available": any(x.get("available") for x in p.get("variants", [])),
            "farm_target": "カウシェファーム収穫対象商品" in p.get("title", ""),
            "new_user_only": "ご新規さん限定" in p.get("title", ""),
            "partner_id": tag("partnerID"), "category_id": tag("categoryID"),
            "product_code": tag("productCode"),
            "image": (p.get("images") or [{}])[0].get("src"),
            "updated_at": p.get("updated_at"),
            "share_link": share_link(p["handle"]),
        }
