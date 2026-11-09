"""MCP server for KAUCHE (カウシェ).

Exposes the catalog, reviews, deals and a browser-based login as MCP tools so Claude
Desktop / Claude Code / any MCP client can query KAUCHE directly. Read-only.

Run:  python3 -m kauche.mcp_server        (stdio transport)
Needs:  pip install "mcp[cli]"  (plus this package on PYTHONPATH)

Login model (no token ever crosses the chat): `kauche_login` starts a local sign-in page
and returns its URL; the user opens it and signs in with Google/Apple; the token is saved
to ~/.cache/kauche-api/account.json (chmod 600). Other tools then work. On expiry the
account-gated tools return a short "please log in again" result.
"""
from __future__ import annotations

try:
    try:
        from mcp.server.fastmcp import FastMCP  # mcp SDK 1.x
    except ModuleNotFoundError:
        from mcp.server import MCPServer as FastMCP  # mcp SDK 2.x (FastMCP renamed)
except ImportError as e:  # pragma: no cover
    raise SystemExit('The MCP SDK is required: pip install "mcp"') from e

from .client import Kauche
from .connect import ConnectError, KaucheAPI
from .account import AccountSession, LoginRequired, SessionExpired
from .weblogin import WebLogin
from .shopify import RateLimited
import urllib.error

mcp = FastMCP("kauche")
_k = Kauche()
_login: WebLogin | None = None

_NEEDS_LOGIN = {
    "status": "login_required",
    "message": "This needs a signed-in KAUCHE account. Call kauche_login, ask the user to "
               "open the returned URL and sign in, then retry.",
}


def _guard(fn):
    try:
        return fn()
    except (LoginRequired, SessionExpired):
        return _NEEDS_LOGIN
    except (RateLimited, urllib.error.HTTPError) as e:
        code = getattr(e, "code", None)
        if isinstance(e, RateLimited) or code == 429:
            return {"status": "rate_limited",
                    "message": "KAUCHE/Shopify is throttling; wait ~1 minute and retry. "
                               "Cached results are reused, so repeats are cheap."}
        return {"status": "error", "message": str(e)}
    except ConnectError as e:
        if e.code in (7, 13, 16) and not AccountSession().logged_in():
            return _NEEDS_LOGIN
        return {"status": "error", "code": e.code, "message": e.message}


# ---- catalog (no auth) ----
@mcp.tool()
def kauche_deals(date: str = "") -> list:
    """Today's (or MMDD) daily-sale collections with their products (Shopify, no login)."""
    import datetime
    cols = _k.collections(all_pages=True)
    mmdd = date or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%m%d")
    out = []
    for c in [c for c in cols if mmdd in c["handle"]][:5]:
        out.append({"handle": c["handle"], "title": c["title"],
                    "products": _k.collection_products(c["handle"], limit=50)})
    return out


@mcp.tool()
def kauche_collections(grep: str = "") -> list:
    """List campaign/sale collections; optional substring filter on handle/title."""
    cols = _k.collections(all_pages=bool(grep))
    if grep:
        g = grep.lower()
        cols = [c for c in cols if g in c["handle"].lower() or g in c["title"].lower()]
    return [{"handle": c["handle"], "title": c["title"], "products_count": c.get("products_count")} for c in cols]


@mcp.tool()
def kauche_collection_products(handle: str, limit: int = 50, available_only: bool = False) -> list:
    """Products in a collection (title, price, compare_at_price, discount, vendor, share link)."""
    rows = _k.collection_products(handle, limit=limit)
    return [r for r in rows if r["available"]] if available_only else rows


@mcp.tool()
def kauche_product(handle_or_url: str, with_reviews: bool = False) -> dict:
    """Product detail (price, variants, images, description, vendor). with_reviews adds the
    KAUCHE rating + reviews. Accepts a handle or a kauche.com share URL."""
    return _k.product(handle_or_url, with_reviews=with_reviews)


# ---- internal API (anonymous ok) ----
@mcp.tool()
def kauche_reviews(product_gid: str, page_token: str = "") -> dict:
    """One page (~10) of user reviews + aggregate rating. product_gid: a Shopify numeric
    id or gid:// string. Pass the returned next_page_token to get the next page."""
    return _guard(lambda: _k.reviews(product_gid, page_token))


@mcp.tool()
def kauche_reviews_pull(product_gid: str, limit: int = 30, min_star: int = 1,
                        max_star: int = 5, max_pages: int = 20) -> dict:
    """Pull many reviews across pages, normalized ({star,message,author,date,images}),
    optionally filtered by star. For competitor research set min_star=1, max_star=2 to
    read only the complaints about a rival product (weaknesses to beat on). Star filtering
    is client-side (no server filter), so on huge products a low-star pull samples the most
    recent max_pages*10 reviews — raise max_pages to dig deeper (~1.5s/page).
    product_gid: a Shopify numeric id or gid:// string."""
    return _guard(lambda: _k.reviews_pull(product_gid, limit=limit, min_star=min_star,
                                          max_star=max_star, max_pages=max_pages))


@mcp.tool()
def kauche_timesale() -> list:
    """Products in the home time sale (日替わりセール)."""
    return _guard(lambda: _k.time_sale())


@mcp.tool()
def kauche_categories() -> list:
    """KAUCHE product categories."""
    return _guard(lambda: _k.categories())


@mcp.tool()
def kauche_coupons() -> dict:
    """The current session's coupons."""
    return _guard(lambda: _k.api.coupons())


# ---- account-gated ----
@mcp.tool()
def kauche_sales_ranking(n: int = 20) -> dict:
    """Best-selling products (needs login)."""
    return _guard(lambda: _k.sales_ranking(n))


@mcp.tool()
def kauche_new_arrivals(n: int = 20) -> dict:
    """Newest products (needs login)."""
    return _guard(lambda: _k.new_arrivals(n))


@mcp.tool()
def kauche_shop_products(partner_id: str, limit: int = 20) -> dict:
    """A seller/shop's products. partner_id is the UUID from a product's partner_id."""
    return _guard(lambda: _k.shop_products(partner_id, limit))


@mcp.tool()
def kauche_win_scan(limit: int = 8, with_price: bool = True, collection: str = "", search: str = "") -> list:
    """Rank the products KAUCHE is actively pushing (home time sale) by a win-score
    (review velocity x rating), for competitor/winning-product research. Reviews are
    coin-rewarded on KAUCHE so review count tracks sales. Returns price/discount, rating,
    reviews in last 4 weeks and lifetime, and a win_candidate flag. Keep limit small."""
    from .win import win_scan
    return _guard(lambda: win_scan(limit=limit, with_price=with_price, collection=collection or None, search=search or None, k=_k))


@mcp.tool()
def kauche_api(method: str, body: dict | None = None) -> dict:
    """Call any KAUCHE Connect-RPC method, e.g. 'customer/v1/GetHomeContent'. See
    references/kauche-endpoints.txt for the full list."""
    return _guard(lambda: KaucheAPI.for_account().call(method, body or {}))


# ---- auth ----
@mcp.tool()
def kauche_login() -> dict:
    """Start a browser login and return a URL. Ask the user to open it and sign in with
    Google or Apple; the token is then saved securely (never shown). After they confirm,
    call kauche_whoami or retry the tool. Needed only for account-gated tools."""
    global _login
    if AccountSession().logged_in():
        return {"status": "already_logged_in"}
    _login = WebLogin()
    url = _login.start(open_browser=True)
    return {
        "status": "awaiting_sign_in",
        "login_url": url,
        "instructions": "Open login_url in a browser, sign in with Google/Apple, then call "
                        "kauche_whoami. The token is saved locally and never shown here.",
    }


@mcp.tool()
def kauche_whoami() -> dict:
    """Current auth state: anonymous, signed-in (with email), or expired."""
    s = AccountSession()
    if not s.logged_in():
        return {"status": "anonymous", "note": "Catalog/reviews/deals work. Call kauche_login for account-gated tools."}
    try:
        s.id_token()
        return {"status": "signed_in", "email": s.email}
    except (LoginRequired, SessionExpired):
        return {"status": "expired", "note": "Call kauche_login to sign in again."}


@mcp.tool()
def kauche_logout() -> dict:
    """Clear the saved session."""
    AccountSession().logout()
    return {"status": "logged_out"}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
