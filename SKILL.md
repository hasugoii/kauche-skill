---
name: kauche
description: Query the Japanese shopping app KAUCHE (カウシェ, com.kauche.kauche) from any agent — product catalog, prices, search, product detail, daily deals, Kauche-Farm target products, user reviews & ratings, sales ranking, new arrivals, time sale, and seller/shop listings — through its reverse-engineered internal API plus its public Shopify storefront. Use for competitor price research, monitoring your own listings, or tracking Kauche sales. Also explains how the app works (coins, coupons, farm, seller fees). Read-only; checkout happens only in the app.
---

# KAUCHE (カウシェ) skill

KAUCHE is a Japanese mobile-only shopping app (KAUCHE Inc., 8M+ downloads). It has
no web shop. This skill gives agents two ways in, reverse-engineered from the app
(v2.164.0):

1. **Shopify storefront** (`kauche.myshopify.com`) — public, no auth. The catalog:
   products, **prices**, product detail, collections, daily-sale buckets. Best for
   competitor prices, your own listings, sale tracking.
2. **Internal Connect-RPC API** (`api.kauche.com`) — anonymous Firebase auth. The
   app-only data: **user reviews & ratings**, home **time sale**, sales **ranking**,
   new arrivals, product categories, **seller/shop** products, coupons.

Checkout, coins, writing reviews, farm actions — all stay in the app. This is read-only.

## Quick start (CLI)

```bash
python3 scripts/kauche.py deals                      # today's dated sale collections (Shopify)
python3 scripts/kauche.py collections --grep higawari
python3 scripts/kauche.py products shiire-higawari-0228 --available
python3 scripts/kauche.py product <handle-or-share-url> --reviews   # Shopify detail + Kauche rating
python3 scripts/kauche.py reviews gid://shopify/Product/15426646638760
python3 scripts/kauche.py timesale                   # home 日替わりセール products
python3 scripts/kauche.py categories                 # kauche.py coupons
python3 scripts/kauche.py shop <partner_id>          # a seller's products
python3 scripts/kauche.py api customer/v1/GetHomeContent '{}'   # any Connect-RPC method
```

Library:
```python
from kauche import Kauche
k = Kauche()
k.collection_products("shiire-higawari-0228", limit=10)          # Shopify, no auth
k.product("https://kauche.com/products/<handle>", with_reviews=True)
k.reviews("gid://shopify/Product/15426646638760")                # ratings + reviews
k.time_sale()
```

Python 3.9+, stdlib only. Add `--json` to any command. First internal-API call does an
anonymous Firebase sign-in (cached in `~/.cache/kauche-api`).

## What works, and what doesn't (be honest with the user)

- **Catalog/prices/detail/collections**: Shopify, reliable, no auth. A few app-exclusive
  items (some time-sale products) are not on the public storefront → 404; detail for
  those isn't retrievable anonymously.
- **Reviews & ratings** (`ListProductFeedbacks`), **time sale** (`GetHomeContent`),
  **categories**, **coupons**, **search settings**: verified working with an anonymous token.
- **Sales ranking / new arrivals / GetProduct**: need a signed-in user (see Login); they return
  `code 13 Internal` for anonymous users — they likely need a signed-in (LINE/Apple/
  Google) account. The CLI surfaces the error cleanly. Don't claim these work anonymously.
- **Search by keyword**: the Shopify predictive endpoint returns `417` for this shop;
  the Kauche text search is farm-quest-scoped. For keyword lookups, browse a collection
  (Shopify) or a ranking/category and filter titles locally. Say which you used.

## Login (for authenticated endpoints)

Sales ranking, new arrivals, GetProduct and your own listings/orders need a signed-in
Firebase user. The account owner can establish a session (Claude never handles your
password — you bring a credential you got yourself):

```bash
python3 scripts/kauche.py login                 # browser login: opens a link, sign in with Google/Apple, token returns automatically
python3 scripts/kauche.py login --refresh-token <firebase-refresh-token>   # headless alternative
python3 scripts/kauche.py whoami                # python3 scripts/kauche.py logout
```

`login` (no args) starts a local page, opens your browser, you sign in with Google or
Apple (Firebase popup), and the token is captured back automatically — no copy-paste.
LINE (custom provider) and `--google-id-token`/`--custom-token`/`--refresh-token` are the
manual alternatives; see `references/internal-api.md`.

After login the same commands (ranking, newarrivals, product) use the signed-in session
automatically (cached in `~/.cache/kauche-api/account.json`, auto-refreshed). LINE flow,
Apple, and provisioning (`CompleteSignIn`) are in `references/internal-api.md`. Phone auth
is not reproducible headlessly. Do login only for your own account.

## Key rules

1. **Rate limits are harsh on both backends.** Shopify 429s after ~10 quick requests
   (blocks minutes); the client paces (`KAUCHE_INTERVAL`) and caches 10 min. The Kauche
   API is paced too. Plan a few requests per question; never crawl.
2. **Prices are JPY, tax included**, strings without decimals (`"4090"` = ¥4,090).
   `compare_at_price` is the 参考価格 (strike-through); discount % is derived.
3. **`vendor` = seller shop**; `partnerID:<uuid>` tag = that shop's id for `shop`/partner calls.
   Products are Shopify; the Kauche API keys them by `shopify_product_gid`.
4. **Share link** `https://kauche.com/products/<handle>` opens the item in the app. Give
   this to users, not the `myshopify.com` URL.
5. Data is a read of public/app endpoints; the app may differ. Not affiliated with KAUCHE.

## Workflows

- **Competitor price / my listing** → `product <handle> --reviews`, or `products <collection>`
  for a batch. Prices from Shopify, rating/reviews from Kauche.
- **What's on sale** → `deals` (dated collections) and `timesale` (home time sale).
- **Reviews of a product** → `reviews <gid>` (get the gid from `product --json` → `product_gid`,
  or from `timesale`). Returns aggregate rating + individual posts.
- **A seller's range** → `shop <partner_id>` (partner_id from a product's `partner_id`).
- **How coins/coupons/farm/selling work** → `references/kauche-app.md` (official FAQ, with URLs).
- **Anything else** → `api <method> <json>` for any of the 157 endpoints in
  `references/kauche-endpoints.txt`.

## Files

- `kauche/` — the library: `auth.py` (anon Firebase), `connect.py` (Connect-RPC client),
  `shopify.py` (storefront), `client.py` (Hybrid facade).
- `scripts/kauche.py` — unified CLI.
- `references/internal-api.md` — endpoints, auth, Connect-RPC, field schemas, what's verified.
- `references/storefront-api.md` — Shopify endpoints, JSON shapes, collection naming, rate limits.
- `references/kauche-app.md` — app features, coin/coupon/farm rules, seller program.
- `references/kauche-endpoints.txt` — all 157 internal endpoints.
- `notes/portal-notes.md` — reverse-engineering traps; append new ones.
