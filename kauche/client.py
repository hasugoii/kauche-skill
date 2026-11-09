"""Hybrid KAUCHE client: Shopify storefront (catalog/prices, no auth) + the
internal Connect-RPC API (reviews, ranking, time sale, shops; anonymous auth)."""
from __future__ import annotations

from .connect import KaucheAPI, ConnectError
from .shopify import ShopifyStorefront, handle_from, share_link


class Kauche:
    def __init__(self):
        self.shop = ShopifyStorefront()
        self._api = None  # lazy: only authenticates when an internal endpoint is used

    @property
    def api(self) -> KaucheAPI:
        if self._api is None:
            self._api = KaucheAPI.for_account()  # signed-in session if present, else anonymous
        return self._api

    # catalog (Shopify, no auth)
    def collections(self, **kw):
        return self.shop.collections(**kw)

    def collection_products(self, handle, **kw):
        return self.shop.collection_products(handle, **kw)

    def product(self, handle_or_url, with_reviews: bool = False) -> dict:
        """Product detail from Shopify; optionally merge KAUCHE rating + reviews."""
        p = self.shop.product(handle_or_url)
        if with_reviews:
            try:
                r = self.api.reviews(p["product_gid"])
                p["rating"] = r.get("product_rating")
                p["reviews"] = r.get("product_feedbacks", [])
            except (ConnectError, Exception) as e:  # keep catalog usable if API fails
                p["reviews_error"] = str(e)
        return p

    # internal API (anonymous auth)
    def reviews(self, product_gid, page_token: str = ""):
        return self.api.reviews(product_gid, page_token)

    def reviews_pull(self, product_gid, limit: int = 30, min_star: int = 1,
                     max_star: int = 5, max_pages: int = 20) -> dict:
        """Walk ListProductFeedbacks across pages and return normalized reviews.

        Great for competitor research: set min_star=1, max_star=2 to pull only the
        complaints (what customers dislike about a rival product) — the weaknesses to
        beat on. Returns {rating (aggregate), count, reviews:[{star,message,author,
        date,images}], pages, next_page_token}. `limit` caps kept reviews; `max_pages`
        caps API calls (each page ~10 feedbacks, newest first).

        Note: the API has no server-side star filter, so star filtering scans pages
        client-side. Low stars are rare (often ~1-2%), so on a product with tens of
        thousands of reviews a 1-2★ pull samples only the most recent `max_pages*10`
        reviews — raise `max_pages` to dig deeper (slower: ~1.5 s/page). Use the
        `next_page_token` in the result to resume where it stopped."""
        kept, token, pages, rating = [], "", 0, None
        while pages < max_pages and len(kept) < limit:
            r = self.api.reviews(product_gid, token)
            if rating is None:
                rating = r.get("product_rating")
            for fb in r.get("product_feedbacks") or []:
                up = fb.get("user_post") or {}
                star = up.get("product_rating_value")
                if star is None or not (min_star <= star <= max_star):
                    continue
                prof = up.get("owner_user_profile") or {}
                kept.append({
                    "star": star,
                    "message": up.get("message"),
                    "author": prof.get("nick_name") or prof.get("display_name"),
                    "date": up.get("post_time"),
                    "images": up.get("image_urls") or [],
                })
                if len(kept) >= limit:
                    break
            pages += 1
            token = r.get("next_page_token") or ""
            if not token:
                break
        return {"rating": rating, "count": len(kept), "pages": pages,
                "next_page_token": token, "reviews": kept}

    def time_sale(self):
        return self.api.time_sale()

    def sales_ranking(self, n: int = 20):
        return self.api.products_by_sales_ranking(n)

    def new_arrivals(self, n: int = 20):
        return self.api.products_by_new_arrival(n)

    def shop_products(self, partner_id, limit: int = 20):
        return self.api.products_by_partner(partner_id, limit)

    def categories(self):
        return self.api.categories()
