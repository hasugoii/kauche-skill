#!/usr/bin/env python3
"""kauche.py — read-only CLI for the KAUCHE (カウシェ) public Shopify storefront.

Stdlib only (Python 3.9+). No login, no API key. Purchases are NOT possible
from here: checkout is app-only. Use `link` to hand a product to the app.

Usage:
  kauche.py collections [--all] [--grep TEXT] [--json]
  kauche.py products COLLECTION_HANDLE [--page N] [--limit N] [--available] [--json]
  kauche.py product HANDLE_OR_URL [--json]
  kauche.py search QUERY [--limit N] [--json]
  kauche.py deals [--date MMDD] [--json]
  kauche.py farm-targets [--json]
  kauche.py link HANDLE_OR_URL
  kauche.py raw PATH            # e.g. raw "/products.json?limit=5&page=3"

Rate limiting: Shopify returns 429 "local_rate_limited" after a burst of
requests from one IP. This script spaces requests (>= REQUEST_INTERVAL s),
retries 429 with backoff, and caches responses for CACHE_TTL seconds.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

STORE = "https://kauche.myshopify.com"
SHARE_BASE = "https://kauche.com/products/"
UA = "kauche-skill/1.0 (+https://github.com/hasugoii/kauche-skill)"
REQUEST_INTERVAL = float(os.environ.get("KAUCHE_INTERVAL", "1.5"))
CACHE_TTL = int(os.environ.get("KAUCHE_CACHE_TTL", "600"))
CACHE_DIR = os.environ.get(
    "KAUCHE_CACHE_DIR", os.path.join(os.path.expanduser("~"), ".cache", "kauche-skill")
)
JST = dt.timezone(dt.timedelta(hours=9))

_last_request = 0.0


def _cache_path(url):
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".json")


def fetch(path, use_cache=True):
    """GET STORE+path, return parsed JSON. Paced, cached, 429-aware."""
    global _last_request
    url = path if path.startswith("http") else STORE + path
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp) and time.time() - os.path.getmtime(cp) < CACHE_TTL:
        with open(cp, encoding="utf-8") as f:
            return json.load(f)
    delays = [0, 5, 10, 20, 40]
    for attempt, extra in enumerate(delays):
        wait = max(0.0, _last_request + REQUEST_INTERVAL - time.time()) + extra
        if wait:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Language": "ja"})
        _last_request = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < len(delays) - 1:
                print(f"[kauche] 429 rate limited, retrying in {delays[attempt+1]}s", file=sys.stderr)
                continue
            raise SystemExit(f"HTTP {e.code} for {url}: {e.read()[:200]!r}")
        data = json.loads(body)
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return data
    raise SystemExit("gave up after repeated 429")


# ---------- helpers ----------

def handle_from(arg):
    """Accept a handle, a kauche.com share URL or a myshopify URL."""
    m = re.search(r"/products/([^/?#]+)", arg)
    return m.group(1) if m else arg.strip()


def share_link(handle):
    return SHARE_BASE + handle


def yen(s):
    try:
        return f"¥{int(float(s)):,}"
    except (TypeError, ValueError):
        return str(s)


def tag_value(tags, key):
    for t in tags or []:
        if t.startswith(key + ":"):
            return t.split(":", 1)[1]
    return None


def summarize_product(p):
    v = p["variants"][0] if p.get("variants") else {}
    price = v.get("price")
    cmp = v.get("compare_at_price")
    off = None
    try:
        if cmp and float(cmp) > float(price):
            off = round(100 * (1 - float(price) / float(cmp)))
    except (TypeError, ValueError):
        pass
    tags = p.get("tags") or []
    return {
        "id": p["id"],
        "handle": p["handle"],
        "title": p["title"],
        "vendor": p.get("vendor"),
        "product_type": p.get("product_type"),
        "price": price,
        "compare_at_price": cmp,
        "discount_pct": off,
        "available": any(x.get("available") for x in p.get("variants", [])),
        "variants": len(p.get("variants", [])),
        "farm_target": "カウシェファーム収穫対象商品" in p.get("title", ""),
        "new_user_only": "ご新規さん限定" in p.get("title", ""),
        "category_id": tag_value(tags, "categoryID"),
        "partner_id": tag_value(tags, "partnerID"),
        "product_code": tag_value(tags, "productCode"),
        "categories": [t for t in tags if ":" not in t],
        "image": (p.get("images") or [{}])[0].get("src"),
        "published_at": p.get("published_at"),
        "updated_at": p.get("updated_at"),
        "share_link": share_link(p["handle"]),
    }


def print_products(rows):
    for r in rows:
        flag = ("🌱" if r["farm_target"] else "") + ("🆕" if r["new_user_only"] else "") + ("" if r["available"] else "✖売切")
        off = f" ({r['discount_pct']}%OFF, 参考{yen(r['compare_at_price'])})" if r["discount_pct"] else ""
        print(f"{yen(r['price'])}{off} {flag} {r['title'][:70]}\n    {r['vendor']} | {r['product_type']} | {r['share_link']}")


def out(args, data, printer):
    if getattr(args, "json", False):
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        printer(data)


MAX_COLLECTION_PAGES = int(os.environ.get("KAUCHE_MAX_COLLECTION_PAGES", "3"))


def load_collections(all_pages=False):
    """Collections, newest-updated first per Shopify. Bounded: never more than
    MAX_COLLECTION_PAGES requests (each page = 1 request, 250 rows)."""
    cols = []
    page = 1
    while True:
        d = fetch(f"/collections.json?limit=250&page={page}")
        cols += d["collections"]
        if len(d["collections"]) < 250 or not all_pages or page >= MAX_COLLECTION_PAGES:
            break
        page += 1
    return cols


# ---------- commands ----------

def cmd_collections(args):
    cols = load_collections(all_pages=args.all)
    if args.grep:
        g = args.grep.lower()
        cols = [c for c in cols if g in c["handle"].lower() or g in c["title"].lower()]
    rows = [{"handle": c["handle"], "title": c["title"], "products_count": c.get("products_count"), "updated_at": c["updated_at"]} for c in cols]

    def pr(rows):
        for c in rows:
            print(f"{c['products_count']:>8}  {c['handle']:<45} {c['title']}")
        if not args.all:
            print(f"(first 250 collections only; --all reads up to {MAX_COLLECTION_PAGES} pages)", file=sys.stderr)
    out(args, rows, pr)


def cmd_products(args):
    d = fetch(f"/collections/{args.collection}/products.json?limit={args.limit}&page={args.page}")
    rows = [summarize_product(p) for p in d["products"]]
    if args.available:
        rows = [r for r in rows if r["available"]]
    out(args, rows, print_products)


def cmd_product(args):
    h = handle_from(args.handle)
    d = fetch(f"/products/{h}.json")
    p = d["product"]
    s = summarize_product(p)
    s["body_html"] = p.get("body_html")
    s["variant_list"] = [
        {"id": v["id"], "title": v["title"], "price": v["price"], "compare_at_price": v.get("compare_at_price"), "available": v.get("available"), "sku": v.get("sku")}
        for v in p.get("variants", [])
    ]
    s["images"] = [i["src"] for i in p.get("images", [])]

    def pr(s):
        print_products([s])
        for v in s["variant_list"]:
            print(f"    variant {v['id']}: {v['title']} {yen(v['price'])} {'在庫あり' if v['available'] else '売切'}")
        text = re.sub(r"<[^>]+>", " ", s["body_html"] or "")
        text = re.sub(r"\s+", " ", text).strip()
        print("    " + text[:1200])
    out(args, s, pr)


def cmd_search(args):
    q = urllib.parse.quote(args.query)
    d = fetch(f"/search/suggest.json?q={q}&resources%5Btype%5D=product&resources%5Blimit%5D={args.limit}&resources%5Boptions%5D%5Bunavailable_products%5D=last")
    prods = d.get("resources", {}).get("results", {}).get("products", [])
    rows = []
    for p in prods:
        rows.append({
            "handle": p.get("handle"),
            "title": p.get("title"),
            "price": p.get("price"),
            "compare_at_price": p.get("compare_at_price_max"),
            "available": p.get("available"),
            "vendor": p.get("vendor"),
            "image": p.get("image"),
            "share_link": share_link(p.get("handle", "")),
        })

    def pr(rows):
        for r in rows:
            print(f"{yen(r['price'])} {'' if r['available'] else '✖売切 '}{r['title'][:80]}\n    {r['vendor']} | {r['share_link']}")
        if not rows:
            print("no results (suggest API only matches title/vendor prefixes; try a shorter Japanese keyword)")
    out(args, rows, pr)


DEAL_PATTERNS = ["higawari", "shiire", "final", "3day", "4day", "5day", "coupon", "sale", "dodon", "dai_sale", "crosscell", "crosssell", "kanshasai"]


def cmd_deals(args):
    today = dt.datetime.now(JST)
    mmdd = args.date or today.strftime("%m%d")
    cols = load_collections(all_pages=True)
    yymmdd = today.strftime("%y") + mmdd
    dated = [c for c in cols if yymmdd in c["handle"] or re.search(rf"(^|[-_]){mmdd}($|[-_])", c["handle"]) or f"{mmdd[:2]}/{mmdd[2:]}" in c["title"]]
    dated = dated[:args.max_fetch]
    yymm = today.strftime("%y%m")
    monthly = [c for c in cols if c["handle"].startswith(yymm) or c["handle"].startswith(f"{yymm[:2]}{yymm[2:]}_")]
    result = {"date": mmdd, "dated_collections": [], "monthly_collections": [{"handle": c["handle"], "title": c["title"], "products_count": c.get("products_count")} for c in monthly]}
    for c in dated:
        prods = fetch(f"/collections/{c['handle']}/products.json?limit=50")["products"]
        result["dated_collections"].append({"handle": c["handle"], "title": c["title"], "products": [summarize_product(p) for p in prods]})

    def pr(r):
        print(f"== Dated collections for {r['date']} ({len(r['dated_collections'])})")
        for c in r["dated_collections"]:
            print(f"\n## {c['title']}  [{c['handle']}]")
            print_products(c["products"])
        print(f"\n== Monthly campaign collections ({len(r['monthly_collections'])})")
        for c in r["monthly_collections"]:
            print(f"  {c['products_count']:>8}  {c['handle']:<30} {c['title']}")
        if not r["dated_collections"]:
            print("No collection handle contains today's MMDD. Dated handles are created manually by Kauche staff; check `collections --grep higawari` for the latest.")
    out(args, result, pr)


def cmd_farm_targets(args):
    cols = load_collections(all_pages=True)
    farm = [c for c in cols if c["handle"].startswith("farm_plant_gift_") or "収穫クーポン" in c["title"]]
    farm = farm[:args.max_fetch]
    result = []
    for c in farm:
        prods = fetch(f"/collections/{c['handle']}/products.json?limit=50")["products"]
        result.append({"handle": c["handle"], "title": c["title"], "products": [summarize_product(p) for p in prods]})

    def pr(r):
        for c in r:
            print(f"\n## {c['title']}  [{c['handle']}]")
            print_products(c["products"])
    out(args, result, pr)


def cmd_link(args):
    print(share_link(handle_from(args.handle)))


def cmd_raw(args):
    json.dump(fetch(args.path, use_cache=False), sys.stdout, ensure_ascii=False, indent=2)
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("collections"); s.add_argument("--all", action="store_true"); s.add_argument("--grep"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_collections)
    s = sub.add_parser("products"); s.add_argument("collection"); s.add_argument("--page", type=int, default=1); s.add_argument("--limit", type=int, default=50); s.add_argument("--available", action="store_true"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_products)
    s = sub.add_parser("product"); s.add_argument("handle"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_product)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=10); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_search)
    s = sub.add_parser("deals"); s.add_argument("--date", help="MMDD, default today JST"); s.add_argument("--max-fetch", type=int, default=5, help="max dated collections to expand (1 request each)"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_deals)
    s = sub.add_parser("farm-targets"); s.add_argument("--max-fetch", type=int, default=5); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_farm_targets)
    s = sub.add_parser("link"); s.add_argument("handle"); s.set_defaults(fn=cmd_link)
    s = sub.add_parser("raw"); s.add_argument("path"); s.set_defaults(fn=cmd_raw)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
