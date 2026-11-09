#!/usr/bin/env python3
"""kauche — CLI for the KAUCHE (カウシェ) shopping app. Read-only.

Two layers (see SKILL.md):
  Shopify storefront (no auth): catalog, prices, product detail, daily-sale buckets.
  Internal API (anonymous Firebase auth): reviews, sales ranking, time sale, shops.

Examples:
  kauche.py deals                               # today's dated sale collections
  kauche.py collections --grep higawari
  kauche.py products shiire-higawari-0228 --available
  kauche.py product https://kauche.com/products/<handle> --reviews
  kauche.py reviews gid://shopify/Product/15426646638760
  kauche.py timesale          kauche.py ranking --n 20     kauche.py categories
  kauche.py shop <partner_id>  kauche.py coupons
  kauche.py api customer/v1/GetHomeContent '{}'   # generic Connect-RPC call

Stdlib only, Python 3.9+. Add --json for machine-readable output.
Rate limits are harsh on both backends; the client paces and caches. Don't crawl.
"""
import argparse
import datetime as dt
import json
import urllib.error
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kauche import (Kauche, KaucheAPI, ConnectError, LoginRequired, SessionExpired,  # noqa: E402
                    share_link, handle_from)

JST = dt.timezone(dt.timedelta(hours=9))


def dump(obj):
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    print()


def yen(s):
    try:
        return f"¥{int(float(s)):,}"
    except (TypeError, ValueError):
        return str(s)


def print_products(rows):
    for r in rows:
        flag = ("🌱" if r.get("farm_target") else "") + ("🆕" if r.get("new_user_only") else "") + ("" if r.get("available", True) else "✖")
        off = f" ({r['discount_pct']}%OFF)" if r.get("discount_pct") else ""
        print(f"{yen(r.get('price'))}{off} {flag} {str(r.get('title',''))[:70]}")
        print(f"    {r.get('vendor')} | {r.get('product_type','')} | {r.get('share_link','')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--auto-login", action="store_true", help="if login is needed/expired, open the browser login automatically then retry")
    sub = ap.add_subparsers(dest="cmd", required=True, parser_class=lambda **kw: argparse.ArgumentParser(parents=[common], **kw))
    sub.add_parser("collections").add_argument("--grep"); sub.choices["collections"].add_argument("--all", action="store_true")
    p = sub.add_parser("products"); p.add_argument("collection"); p.add_argument("--limit", type=int, default=50); p.add_argument("--page", type=int, default=1); p.add_argument("--available", action="store_true")
    p = sub.add_parser("product"); p.add_argument("handle"); p.add_argument("--reviews", action="store_true")
    p = sub.add_parser("deals"); p.add_argument("--date")
    sub.add_parser("link").add_argument("handle")
    p = sub.add_parser("reviews"); p.add_argument("product"); p.add_argument("--page-token", default="")
    sub.add_parser("timesale")
    sub.add_parser("categories")
    sub.add_parser("coupons")
    p = sub.add_parser("ranking"); p.add_argument("--n", type=int, default=20)
    p = sub.add_parser("newarrivals"); p.add_argument("--n", type=int, default=20)
    p = sub.add_parser("shop"); p.add_argument("partner_id"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("api"); p.add_argument("method"); p.add_argument("body", nargs="?", default="{}")
    p = sub.add_parser("login", help="establish a signed-in session (browser by default)")
    p.add_argument("--web", action="store_true", help="browser login (default): opens a link, returns the token")
    p.add_argument("--port", type=int, default=0, help="local port for --web (default: random)")
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--refresh-token", help="Firebase refresh token from your own session")
    g.add_argument("--custom-token", help="Firebase custom token (e.g. from LINE CompleteLineLogin)")
    g.add_argument("--google-id-token", help="Google OpenID id_token")
    g.add_argument("--apple-id-token", help="Apple id_token")
    p.add_argument("--signup", action="store_true", help="also run customer/v1/CompleteSignIn to provision your KAUCHE profile")
    p = sub.add_parser("win", help="rank products KAUCHE is pushing by a review-velocity win-score"); p.add_argument("--limit", type=int, default=8); p.add_argument("--no-price", action="store_true")
    sub.add_parser("logout")
    sub.add_parser("whoami")
    args = ap.parse_args()
    k = Kauche()
    prog = "python3 " + os.path.relpath(__file__)

    def login_hint(why):
        print(f"\n🔑 {why}", file=sys.stderr)
        print(f"   Ask the user to run:  {prog} login", file=sys.stderr)
        print("   A browser opens; they sign in with Google/Apple; the token is saved "
              "securely (never shown). Then retry this command.", file=sys.stderr)

    def do_retry():
        # optional convenience: --auto-login re-runs web login then retries once
        if getattr(args, "auto_login", False):
            from kauche.weblogin import run_web_login
            run_web_login()
            k._api = None  # drop cached anon/expired session
            run(args, k)
            return True
        return False

    try:
        run(args, k)
    except LoginRequired:
        if not do_retry():
            login_hint("This needs a signed-in KAUCHE account (not logged in yet).")
            sys.exit(2)
    except SessionExpired:
        if not do_retry():
            login_hint("Your KAUCHE session expired. Log in again to continue.")
            sys.exit(2)
    except ConnectError as e:
        print(f"KAUCHE API error: {e}", file=sys.stderr)
        from kauche import AccountSession
        if e.code in (7, 13, 16) and not AccountSession().logged_in():
            login_hint("This needs a signed-in KAUCHE account (you are anonymous now).")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        host = (e.url or "").split("/")[2] if "://" in (e.url or "") else "?"
        detail = ""
        try:
            detail = " — " + e.read().decode(errors="replace")[:200]
        except Exception:
            pass
        if "myshopify" in host:
            detail = " — product/collection may be app-exclusive (not on the public storefront)." or detail
        print(f"HTTP {e.code} from {host}{detail}", file=sys.stderr)
        sys.exit(1)


def run(args, k):
    prog = "python3 " + os.path.relpath(__file__)
    if args.cmd == "collections":
        cols = k.collections(all_pages=bool(args.all))
        if args.grep:
            g = args.grep.lower()
            cols = [c for c in cols if g in c["handle"].lower() or g in c["title"].lower()]
        rows = [{"handle": c["handle"], "title": c["title"], "products_count": c.get("products_count")} for c in cols]
        if args.json:
            dump(rows)
        else:
            for c in rows:
                print(f"{c['products_count']:>8}  {c['handle']:<42} {c['title']}")

    elif args.cmd == "products":
        rows = k.collection_products(args.collection, limit=args.limit, page=args.page)
        if args.available:
            rows = [r for r in rows if r["available"]]
        dump(rows) if args.json else print_products(rows)

    elif args.cmd == "product":
        p = k.product(args.handle, with_reviews=args.reviews)
        if args.json:
            dump(p)
        else:
            print_products([p])
            for v in p.get("variants_detail", []):
                print(f"    variant {v['id']}: {yen(v['price'])} {'在庫' if v['available'] else '売切'}")
            if "rating" in p:
                print(f"    rating: {p['rating']}  reviews: {len(p.get('reviews', []))}")

    elif args.cmd == "deals":
        today = dt.datetime.now(JST)
        mmdd = args.date or today.strftime("%m%d")
        cols = k.collections(all_pages=True)
        dated = [c for c in cols if mmdd in c["handle"]][:5]
        result = []
        for c in dated:
            result.append({"handle": c["handle"], "title": c["title"],
                           "products": k.collection_products(c["handle"], limit=50)})
        if args.json:
            dump(result)
        elif not result:
            print(f"No dated collection for {mmdd}. Try: collections --grep higawari")
        else:
            for c in result:
                print(f"\n## {c['title']} [{c['handle']}]")
                print_products(c["products"])

    elif args.cmd == "link":
        print(share_link(handle_from(args.handle)))

    elif args.cmd == "reviews":
        r = k.reviews(args.product, args.page_token)
        if args.json:
            dump(r)
        else:
            print(f"rating: {r.get('product_rating')}")
            for fb in r.get("product_feedbacks", []):
                up = fb.get("user_post", {})
                print(f"  ★{up.get('product_rating_value','?')} {up.get('owner_user_profile',{}).get('nick_name','')}: {str(up.get('message','')).strip()[:120]}")

    elif args.cmd == "timesale":
        dump(k.time_sale())
    elif args.cmd == "categories":
        dump(k.categories())
    elif args.cmd == "coupons":
        dump(k.api.coupons())
    elif args.cmd == "ranking":
        dump(k.sales_ranking(args.n))
    elif args.cmd == "newarrivals":
        dump(k.new_arrivals(args.n))
    elif args.cmd == "shop":
        dump(k.shop_products(args.partner_id, args.limit))
    elif args.cmd == "win":
        from kauche.win import win_scan, WIN_VELOCITY, RATING_GATE
        rows = win_scan(limit=args.limit, with_price=not args.no_price, k=k)
        if args.json:
            dump(rows)
        else:
            print(f"win-score = reviews_28d x rating_factor; candidate = >={WIN_VELOCITY}/4wk & rating>={RATING_GATE}\n")
            for r in rows:
                star = "\u2b50" if r["win_candidate"] else "  "
                price = yen(r["price"]) if r["price"] else "?"
                off = f" -{r['discount_pct']}%" if r.get("discount_pct") else ""
                print(f"{star} score {r['score']:>6}  {price}{off}  \u2605{r['rating'] or '?'} "
                      f"({r['reviews_28d'] or 0}/4wk, {r['reviews_total'] or 0} total)  {(r['title'] or r['handle'])[:48]}")
                print(f"        {r['vendor'] or ''}  {r['share_link']}")

    elif args.cmd == "api":
        dump(KaucheAPI.for_account().call(args.method, json.loads(args.body)))

    elif args.cmd == "login":
        from kauche import AccountSession
        if args.refresh_token:
            s = AccountSession.from_refresh_token(args.refresh_token)
        elif args.web or not (args.custom_token or args.google_id_token or args.apple_id_token):
            from kauche.weblogin import run_web_login
            s = run_web_login(port=args.port)
        elif args.custom_token:
            s = AccountSession.from_custom_token(args.custom_token)
        elif args.google_id_token:
            s = AccountSession.from_google_id_token(args.google_id_token)
        else:
            s = AccountSession.from_apple_id_token(args.apple_id_token)
        who = f" as {s.email}" if getattr(s, "email", None) else ""
        print(f"\u2705 Logged in{who}. Session saved to ~/.cache/kauche-api/account.json "
              "(chmod 600) and auto-refreshed. The token is not printed.")
        if args.signup:
            try:
                KaucheAPI(auth=s).complete_signin()
                print("CompleteSignIn ok (KAUCHE profile provisioned).")
            except ConnectError as e:
                print(f"CompleteSignIn: {e}", file=sys.stderr)

    elif args.cmd == "logout":
        from kauche import AccountSession
        AccountSession().logout()
        print("logged out.")

    elif args.cmd == "whoami":
        from kauche import AccountSession
        s = AccountSession()
        if not s.logged_in():
            print(f"anonymous. Catalog/reviews/deals work. For ranking/your listings, run:  {prog} login")
        else:
            who = f" ({s.email})" if s.email else ""
            try:
                s.id_token()  # validates / refreshes
                print(f"signed in{who}; session valid, account-gated endpoints enabled.")
            except (LoginRequired, SessionExpired):
                print(f"session for{who or ' your account'} expired. Run:  {prog} login")


if __name__ == "__main__":
    main()
