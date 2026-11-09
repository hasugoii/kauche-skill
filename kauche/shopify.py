"""KAUCHE catalog via its public Shopify storefront (kauche.myshopify.com).

No auth. Shopify's standard Online Store JSON endpoints are open, so this is the
reliable path for catalog, prices, product detail, collections and the daily-sale
buckets. Checkout is app-only. Rate limit is harsh (~10 quick requests -> 429 for
minutes); requests are paced and cached. See references/storefront-api.md.
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

# Process-wide Shopify throttle: one request at a time, with a shared cooldown after a 429
# so parallel callers (e.g. several MCP tool calls) queue instead of bursting into the limit.
_LOCK = threading.Lock()
_STATE = {"last": 0.0, "cooldown_until": 0.0}


class RateLimited(Exception):
    """Shopify returned 429 past our retries; back off and try again shortly."""

STORE = "https://kauche.myshopify.com"
SHARE_BASE = "https://kauche.com/products/"
UA = "kauche-skill/1.0 (+https://github.com/hasugoii/kauche-skill)"
INTERVAL = float(os.environ.get("KAUCHE_INTERVAL", "2.5"))
CACHE_TTL = int(os.environ.get("KAUCHE_CACHE_TTL", "600"))
CACHE_DIR = os.environ.get("KAUCHE_CACHE_DIR", os.path.join(os.path.expanduser("~"), ".cache", "kauche-api", "shopify"))


def handle_from(arg: str) -> str:
    m = re.search(r"/products/([^/?#]+)", arg or "")
    return m.group(1) if m else (arg or "").strip()


def share_link(handle: str) -> str:
    return SHARE_BASE + handle


class ShopifyStorefront:
    def __init__(self, interval: float = INTERVAL, cache_ttl: int = CACHE_TTL):
        self.interval = interval
        self.cache_ttl = cache_ttl
        self._last = 0.0

    def _cache(self, url):
        return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".json")

    def _http(self, url: str, accept: str) -> str:
        """One throttled GET. Serialized process-wide; honors Retry-After; shared cooldown
        after a 429 so everyone backs off together. Raises RateLimited if it can't get through."""
        headers = {"User-Agent": UA, "Accept": accept, "Accept-Language": "ja"}
        with _LOCK:
            for attempt in range(6):
                now = time.time()
                wait = max(_STATE["cooldown_until"] - now, _STATE["last"] + self.interval - now, 0.0)
                if wait:
                    time.sleep(wait + random.uniform(0, 0.4))  # jitter
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

    def collections(self, all_pages: bool = False, max_pages: int = 3):
        cols, page = [], 1
        while True:
            d = self.fetch(f"/collections.json?limit=250&page={page}")
            cols += d["collections"]
            if len(d["collections"]) < 250 or not all_pages or page >= max_pages:
                break
            page += 1
        return cols

    def collection_products(self, handle: str, limit: int = 50, page: int = 1):
        d = self.fetch(f"/collections/{handle}/products.json?limit={limit}&page={page}")
        return [self.summarize(p) for p in d["products"]]

    def product(self, handle_or_url: str) -> dict:
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
        s["product_gid"] = p["id"]  # numeric Shopify product id -> feed to KaucheAPI.reviews()
        return s

    def search(self, query: str, limit: int = 12) -> list:
        """Keyword search via the storefront search page (anonymous). Returns
        [{id, handle, title, price}]. The predictive JSON API is disabled (417) for this
        shop, so this parses the HTML results; id is the Shopify numeric product id."""
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
