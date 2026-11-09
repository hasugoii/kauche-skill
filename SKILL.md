---
name: kauche
description: Browse, search and monitor the Japanese shopping app KAUCHE (カウシェ, com.kauche.kauche) from any agent — daily deals (日替わりセール), coupon collections, Kauche Farm harvest-target products, product details and app share links — through its public Shopify storefront. Also explains how the app works (coins, coupons, farm quests, seller fees). Use when a task mentions Kauche/カウシェ, Kauche Farm/カウシェファーム, or wants Japanese food/daily-goods deals from this app. Read-only; checkout happens only inside the app.
---

# KAUCHE (カウシェ) skill

KAUCHE is a Japanese mobile-only social-commerce app (iOS/Android, KAUCHE Inc.,
8M+ downloads). It has **no web shop and no public API**, but its catalog lives on a
Shopify store, `kauche.myshopify.com`, whose standard storefront JSON endpoints are
open. This skill wraps those endpoints and documents the app's mechanics.

What you **can** do here: list collections, list products in a collection, get a
product with price / 参考価格 / stock / description / images, find today's dated sale
collections, find Kauche-Farm harvest-target products, and produce a share link that
opens the product in the app.

What you **cannot** do here: log in, see a user's coins/coupons/farm, add to cart, or
buy. Every product page on the web says 「アプリで購入」. Hand the user the share link.

## Quick start

```bash
python3 scripts/kauche.py collections --grep higawari     # dated daily-sale collections
python3 scripts/kauche.py deals                            # today's (JST) dated sales + monthly campaigns
python3 scripts/kauche.py products shiire-higawari-0228 --available
python3 scripts/kauche.py product <handle-or-share-url>
python3 scripts/kauche.py farm-targets                     # 100%OFF harvest-coupon target products
python3 scripts/kauche.py link <handle>                    # -> https://kauche.com/products/<handle>
python3 scripts/kauche.py raw "/products.json?limit=5&page=2"
```

Add `--json` to any command for machine-readable output. Python 3.9+, stdlib only.

## Rules that matter

1. **Rate limit is harsh.** Shopify answers `429 local_rate_limited` / `TOO_MANY_REQUESTS`
   after a burst (roughly 8–10 quick requests from one IP) and then blocks for
   several minutes. The script paces requests (`KAUCHE_INTERVAL`, default 1.5 s),
   retries with backoff and caches for 10 min (`KAUCHE_CACHE_TTL`). Do not loop over
   thousands of products. Plan 1–5 requests per user question.
2. **Prices are JPY, tax included**, given as strings without decimals (`"4090"` = ¥4,090).
   `compare_at_price` is the 参考価格 shown as a strike-through; discount % is derived.
3. **`vendor` is the seller shop name** (Kauche is a marketplace; each 販売会社 ships its own
   orders). `product_type` is the top-level category in Japanese.
4. **Tags carry structured IDs**: `categoryID:<n>`, `partnerID:<uuid>`, `productCode:<code>`,
   plus plain Japanese category breadcrumbs.
5. **Title markers**: `【カウシェファーム収穫対象商品】` = can be claimed with a farm
   100%OFF coupon; `【ご新規さん限定商品】` = first-purchase-only price (often ¥50).
6. **Collections are campaign buckets, not categories.** Handles follow staff naming:
   `shiire-higawari-MMDD` (daily sale), `3day-/4day-/5day-MMDD` (multi-day sale),
   `shiire-final-MMDD`, `*coupon-NNoff`, `YYMM_dodonto` / `YYMM_dai_sale` (monthly),
   `YYMM_crosscell` (water-reward campaign), `farm_plant_gift_<uuid>` (farm coupon
   targets), `beisia_*` (coupon-eligible). Dated handles are created by hand, so
   `deals` may find nothing for a given day — then show the latest `higawari` ones.
7. **Search**: `search/suggest.json` currently returns `417 Unsupported buyer locale`
   on this shop. Treat `search` as best-effort; the reliable path is
   collection → products → filter by title locally. See `references/storefront-api.md`.
8. **Share link** `https://kauche.com/products/<handle>` is what the app itself uses
   when a user shares; it opens in the app (universal link) or falls back to the
   web mirror. Always give this link, never the `myshopify.com` URL.
9. Be honest about freshness: data is a 10-minute cache of a public mirror. Stock,
   price and whether a product is still a quest/farm target can differ in the app.

## Workflows

**"What's on sale today on Kauche?"** → `deals` (optionally `--date MMDD`). Summarize
by discount % and availability, link each item with its share link.

**"Find X on Kauche"** → try `search X`; if 417/empty, pick a likely collection
(`collections --grep` on a campaign word, or the big coupon collections such as
`2000円以下の商品一覧`, `beisia_20-off`), run `products <handle> --limit 250 --json`
and filter titles/tags locally. Say which collections you looked in.

**"Which products can I get free with my farm coupon?"** → `farm-targets`, plus
`references/kauche-app.md` section *Farm* for the coupon rules (30-day validity,
shipping may still be charged, cannot be applied after ordering).

**"How does Kauche Farm / coins / coupons work?"** → answer from
`references/kauche-app.md` (sourced from the official FAQ, with URLs). Do not invent
reward amounts.

**"Should I sell on Kauche?"** → `references/kauche-app.md` section *Seller program*
(0 fixed fee, 10% sales + 3.5% payment fee).

## Files

- `scripts/kauche.py` — the CLI (stdlib only).
- `references/storefront-api.md` — endpoints, JSON shapes, tag semantics, rate-limit notes.
- `references/kauche-app.md` — app features, coin/coupon/farm rules, seller program, hostnames.
- `notes/portal-notes.md` — traps found while reverse-engineering; add yours there.
