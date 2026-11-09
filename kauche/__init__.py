"""kauche — reverse-engineered client for the KAUCHE (カウシェ) shopping app.

Two layers:
- ShopifyStorefront: public Shopify catalog (prices, products, collections). No auth.
- KaucheAPI: the app's internal Connect-RPC API (reviews, ranking, time sale, shops).
  Anonymous Firebase auth; see auth.py. Read-only use; checkout stays in the app.

Quick start:
    from kauche import Kauche
    k = Kauche()
    k.collection_products("shiire-higawari-0228", limit=10)   # Shopify, no auth
    k.reviews("gid://shopify/Product/15426646638760")          # KAUCHE reviews (anon auth)
    k.time_sale()
"""
from .client import Kauche
from .connect import KaucheAPI, ConnectError, gid
from .shopify import ShopifyStorefront, handle_from, share_link
from .auth import FirebaseAnonymousAuth
from .account import AccountSession

__all__ = ["Kauche", "KaucheAPI", "ConnectError", "gid",
           "ShopifyStorefront", "handle_from", "share_link", "FirebaseAnonymousAuth", "AccountSession"]
__version__ = "0.3.0"
