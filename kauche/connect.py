"""Client for KAUCHE's internal app API (api.kauche.com).

Reverse-engineered from the Android app v2.164.0. The API is **Connect-RPC**
(connectrpc.com) over HTTP POST: one URL per method, JSON request and response
bodies, gRPC-style error envelopes `{"code":N,"message":"...","details":[]}`.

- Base: https://api.kauche.com/api
- Method path: `<service>/v1/<Method>` e.g. `customer/v1/GetHomeContent`
- Request body: JSON matching the protobuf request message (snake_case fields).
- Auth: `Authorization: Bearer <firebase-anon-id-token>` (see auth.py). No App Check.
- Content-Type / Accept: application/json.

Field names come from the decompiled protobuf messages; see
references/internal-api.md for the full endpoint + field map and which methods are
verified to work anonymously. Methods marked VERIFIED returned 200 in testing on
2026-11-09; others are mapped from the APK but may need a signed-in (non-anonymous)
user and can return code 13 (Internal) or 7 (PermissionDenied) for guests.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .auth import FirebaseAnonymousAuth

BASE = "https://api.kauche.com/api"
APP_VERSION = "2.164.0"
USER_AGENT = f"com.kauche.kauche/{APP_VERSION} (Android; kauche-skill)"


class ConnectError(Exception):
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"HTTP {status} connect-code={code}: {message}")


def gid(product_or_variant_id, kind: str = "Product") -> dict:
    """Build a Shopify GID message, e.g. gid(15426646638760) ->
    {"gid":"gid://shopify/Product/15426646638760"}. Accepts a bare numeric id or a
    full gid:// string. kind is "Product" or "ProductVariant"."""
    s = str(product_or_variant_id)
    if not s.startswith("gid://"):
        s = f"gid://shopify/{kind}/{s}"
    return {"gid": s}


class KaucheAPI:
    """Thin Connect-RPC client with helpers for the useful customer endpoints."""

    def __init__(self, auth=None, interval: float = 0.6):
        # auth is any object with .id_token(): FirebaseAnonymousAuth or AccountSession.
        self.auth = auth or FirebaseAnonymousAuth()
        self.interval = interval
        self._last = 0.0

    @classmethod
    def for_account(cls, **kw) -> "KaucheAPI":
        """Use the persisted signed-in session if present, else anonymous."""
        from .account import AccountSession
        s = AccountSession()
        return cls(auth=s if s.logged_in() else None, **kw)

    # ---- core ----
    def call(self, method: str, body: dict | None = None) -> dict:
        """POST one Connect method. `method` is like 'customer/v1/GetHomeContent'."""
        wait = self._last + self.interval - time.time()
        if wait > 0:
            time.sleep(wait)
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(
            f"{BASE}/{method}", data=data, method="POST",
            headers={
                "Authorization": "Bearer " + self.auth.id_token(),
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._last = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                j = json.loads(raw)
                raise ConnectError(e.code, j.get("code"), j.get("message", raw))
            except ValueError:
                raise ConnectError(e.code, None, raw[:300])

    def get(self, method: str, path: str = "") -> dict:
        """GET-style Connect call for idempotent methods exposed over GET
        (e.g. 'customer/v1/coupons')."""
        wait = self._last + self.interval - time.time()
        if wait > 0:
            time.sleep(wait)
        url = f"{BASE}/{method}" + (("/" + path) if path else "")
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self.auth.id_token(),
            "User-Agent": USER_AGENT, "Accept": "application/json",
        })
        self._last = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise ConnectError(e.code, None, e.read().decode(errors="replace")[:300])

    # ---- VERIFIED helpers (worked anonymously 2026-11-09) ----
    def home(self) -> dict:
        """GetHomeContent: home sections incl. time_sale_section with products."""
        return self.call("customer/v1/GetHomeContent", {})

    def time_sale(self) -> list:
        """Products currently on the home time sale (日替わりセール)."""
        sec = self.home().get("time_sale_section", {})
        return sec.get("time_sale_products", [])

    def reviews(self, product_gid, page_token: str = "") -> dict:
        """ListProductFeedbacks: user reviews + aggregate rating for a product.
        product_gid: numeric Shopify product id or full gid:// string."""
        body = {"shopify_product_gid": gid(product_gid)}
        if page_token:
            body["page_token"] = page_token
        return self.call("customer/v1/ListProductFeedbacks", body)

    def categories(self) -> list:
        """ListProductCategories."""
        return self.call("customer/v1/ListProductCategories", {}).get("product_categories", [])

    def search_settings(self) -> dict:
        """product_search_settings: recommended search terms, filters."""
        return self.get("customer/v1/product_search_settings")

    def coupons(self) -> dict:
        """The (anonymous) user's available coupons."""
        return self.get("customer/v1/coupons")

    # ---- MAPPED helpers (fields from APK; may need a real user) ----
    def product(self, product_gid=None, handle: str = None, encoded_id: str = None) -> dict:
        """GetProduct. One of: product_gid (Shopify id), handle, encoded_id.
        NOTE: returned code 13 for anonymous users in testing; prefer the Shopify
        storefront for product detail and use reviews() for ratings."""
        body = {}
        if product_gid is not None:
            body["shopify_product_gid"] = gid(product_gid)
        if handle:
            body["product_handle"] = handle
        if encoded_id:
            body["encoded_product_id"] = encoded_id
        return self.call("customer/v1/GetProduct", body)

    def products_by_partner(self, partner_id: str, limit: int = 20, page_token: str = "") -> dict:
        """ListProductsByPartner: a seller/shop's products. partner_id is a UUID
        (see tag partnerID:<uuid> on storefront products, or customer/v1/partners/{id})."""
        return self.call("customer/v1/ListProductsByPartner",
                         {"partner_id": partner_id, "limit": limit, "page_token": page_token})

    def products_by_sales_ranking(self, no_of_products: int = 20, page_token: str = "") -> dict:
        """ListProductsBySalesRanking (1..200)."""
        return self.call("customer/v1/ListProductsBySalesRanking",
                         {"no_of_products": no_of_products, "page_token": page_token})

    def products_by_new_arrival(self, no_of_products: int = 20, page_token: str = "") -> dict:
        """ListProductsByNewArrival (1..200)."""
        return self.call("customer/v1/ListProductsByNewArrival",
                         {"no_of_products": no_of_products, "page_token": page_token})

    def partner(self, partner_id: str) -> dict:
        """GET customer/v1/partners/{id}: shop/seller detail."""
        return self.get("customer/v1/partners", partner_id)

    # ---- account provisioning / LINE login (account owner only) ----
    def complete_signin(self, body: dict | None = None) -> dict:
        """customer/v1/CompleteSignIn: provision the KAUCHE customer record for the
        current Firebase user. Run once after a real (Google/LINE) sign-in. This is a
        write that creates your KAUCHE guest/customer profile — run it yourself only."""
        return self.call("customer/v1/CompleteSignIn", body or {})

    def start_line_login(self, channel_id: str, device_uuid: str) -> dict:
        """account/v1/StartLineLogin -> {nonce_id, nonce, channel_id}. Use `nonce` when
        you perform LINE login in the LINE app/SDK yourself; keep `nonce_id`."""
        return self.call("account/v1/StartLineLogin", {"channel_id": channel_id, "device_uuid": device_uuid})

    def complete_line_login(self, nonce_id: str, line_id_token: str) -> str:
        """account/v1/CompleteLineLogin -> firebase_custom_token. Feed it to
        AccountSession.from_custom_token. `line_id_token` is the OIDC id_token LINE gives
        you after you authorize with the nonce from start_line_login."""
        r = self.call("account/v1/CompleteLineLogin", {"nonce_id": nonce_id, "id_token": line_id_token})
        return r["firebase_custom_token"]
