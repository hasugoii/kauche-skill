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
