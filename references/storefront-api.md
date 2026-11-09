# Kauche public storefront (Shopify) — endpoint reference

Verified 2026-11-09 against `https://kauche.myshopify.com`. Everything here is the
standard Shopify Online Store surface; nothing is Kauche-specific except the data.

## Hosts

| Host | What | Notes |
|---|---|---|
| `kauche.myshopify.com` | Shopify storefront, theme "Taste" 4.0.1 | JSON endpoints below work here |
| `kauche.com` | Firebase-hosted landing page | `/products/<handle>` **301 → myshopify** (this is the share-link format). `/products.json` etc. return Firebase 404 — do not call JSON on this host |
| `pages.kauche.com` | Notion/Bullet-published info pages | `/farm`, `/missions`, `/coupons`, `/campaigns`, `/coin`, `/rank`, `/guide`, `/kauche-de-pon` … |
| `faq.kauche.com` | Helpfeel FAQ | rule source for coins / farm / coupons |
| `seller.kauche.com` | HubSpot seller site | fees, ads, logistics |
| `about.kauche.com` | ToS, privacy, 特定商取引法 | |
| `api.kauche.com` | resolves (Fastly) | the mobile app's private API; not documented, not used by this skill |

## Endpoints (GET, no auth)

| Path | Returns | Tested |
|---|---|---|
| `/collections.json?limit=250&page=N` | `{collections:[{id,handle,title,products_count,updated_at,published_at,...}]}` | page 1 = 250 rows; more pages exist |
| `/collections/<handle>/products.json?limit=250&page=N` | `{products:[...]}` | ✅ |
| `/products.json?limit=250&page=N` | all products, unordered | ✅ but the catalog is in the millions; never crawl |
| `/products/<handle>.json` | `{product:{...}}` full product | ✅ |
| `/products/<handle>.js` | same, Ajax-API shape (prices in minor units) | returned 429 while throttled; untested when calm |
| `/search/suggest.json?q=…&resources[type]=product` | predictive search | ❌ `417 Unsupported buyer locale` (with and without `Accept-Language: ja`) |
| `/search?q=…&type=product` (HTML) | search results page | untested (throttled) |
| `/products/<handle>` (HTML) | product page, shows 「アプリで購入」 | ✅ 200, ~200 KB |
| `/cart/<variant_id>:<qty>` | cart permalink | **not tested on purpose** — checkout is app-only; do not try to buy from the web |

## Product JSON shape (`products.json` / `<handle>.json`)

```
id, title, handle (uuid), body_html, published_at, created_at, updated_at,
vendor            -> seller shop name, e.g. "スリーピースカウシェ店", "ICHIMIZU"
product_type      -> top category, e.g. "キッチン用品・食器・調理器具"
tags              -> ["categoryID:100817", "partnerID:<uuid>", "productCode:K14174-2",
                      "productControlCode:k14174-2", "のれん", "インテリア・寝具・収納", ...]
variants[]        -> {id, title, price:"4090", compare_at_price:"4158", available, sku,
                      requires_shipping, taxable:false, grams, position, updated_at}
images[]          -> {src (cdn.shopify.com), width, height, position}
options[]         -> usually [{name:"Title", values:["Default Title"]}]  (single variant)
```

Observed on a 250-product page: 100 % single-variant, ~50 % `available`, every
product has `compare_at_price`. `taxable:false` + Japanese market ⇒ prices are tax-included.

## Collection naming conventions (staff-made, observed 2026-11)

| Handle pattern | Meaning |
|---|---|
| `shiire-higawari-MMDD` | 日替わり！売れ筋商品が特別タイムセール (daily sale, until 24:00) |
| `3day-MMDD`, `4day-higawari-MMDD`, `5day-MMDD` | multi-day sale series, "N日目" in title |
| `shiire-final-MMDD` | 在庫限りのファイナルセール |
| `shiire-MMDDcoupon-NNoff`, `MMDD-shiire-NNoff` | products eligible for an NN%OFF coupon |
| `beisia_10-off`, `beisia_20-off` | large coupon-eligible pools (1k–4k products) |
| `YYMM_dodonto`, `YYMM-kanshasai`, `YYMM_dai_sale` | month-end 感謝祭 / 大セール祭 (tens of thousands of products) |
| `YYMM_crosscell` / `crosssell`, `N-bizops-great-value` | 水がもらえるキャンペーン — buying earns farm water |
| `farm_plant_gift_<uuid>` | harvest-coupon target products for one crop (title "<brand>の収穫クーポン対象商品") |
| `カウシェファーム用-<crop>対象商品コレクション` | marked `[使っていない]` (unused) — ignore |
| `2000円以下の商品一覧`, `削除不可クーポン用…` | internal coupon-eligibility pools |

`products_count` on big pools reaches 10^5–10^6, so the catalog itself is very large.

## Rate limiting (measured)

- ~8–10 requests inside ~20 s from one IP ⇒ `429` with body `local_rate_limited`
  (HTML/JS routes) or `{"errors":[{"extensions":{"code":"TOO_MANY_REQUESTS"}}]}` (JSON).
- The block persisted through 5 + 10 + 20 + 40 s retries, i.e. several minutes.
- Mitigation in `scripts/kauche.py`: ≥1.5 s spacing, backoff, 10-min disk cache
  (`~/.cache/kauche-skill`). Set `KAUCHE_INTERVAL=3` when sharing an IP with other jobs.


## Throttle (client-side, v0.10)

To avoid Shopify 429s the client now:
- serializes all storefront requests process-wide (one at a time) so parallel MCP tool
  calls queue instead of bursting;
- honors the `Retry-After` header and keeps a shared cooldown after a 429 (all callers back
  off together);
- spaces requests `KAUCHE_INTERVAL` seconds apart (default 2.5) with jitter, and caches
  200s for 10 min;
- raises `RateLimited` after retries; the CLI exits 3 with a friendly message and the MCP
  tools return `{"status":"rate_limited"}` instead of crashing.

Reviews/categories/etc. go through the KAUCHE Connect API (separate, more generous limit),
so the Shopify limit mainly bites on catalog/search/collection calls — keep those few.
