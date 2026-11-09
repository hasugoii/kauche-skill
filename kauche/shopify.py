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
import re
import time
import urllib.error
import urllib.parse
import urllib.request

STORE = "https://kauche.myshopify.com"
SHARE_BASE = "https://kauche.com/products/"
UA = "kauche-skill/1.0 (+https://github.com/hasugoii/kauche-skill)"
INTERVAL = float(os.environ.get("KAUCHE_INTERVAL", "1.5"))
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

    def fetch(self, path: str, use_cache: bool = True) -> dict:
        url = path if path.startswith("http") else STORE + path
        cp = self._cache(url)
        if use_cache and os.path.exists(cp) and time.time() - os.path.getmtime(cp) < self.cache_ttl:
            with open(cp, encoding="utf-8") as f:
                return json.load(f)
        for attempt, extra in enumerate([0, 5, 10, 20, 40]):
            wait = max(0.0, self._last + self.interval - time.time()) + extra
            if wait:
                time.sleep(wait)
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Language": "ja"})
            self._last = time.time()
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 4:
                    continue
                raise
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(cp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return data
        raise RuntimeError("Shopify rate limit: gave up after retries")

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
