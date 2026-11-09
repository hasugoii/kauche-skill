# Winning-product research method (KAUCHE)

Goal: competitor research + spotting products worth selling, from the reverse-engineered
API. KAUCHE rewards reviews with coins, so **review count tracks real purchases** — the
core signal here.

## Signals

| Signal | Source | Meaning |
|---|---|---|
| review velocity (28d) | `kauche_reviews` → `product_feedbacks[].user_post.post_time` | current demand / sales pace |
| lifetime reviews | `product_rating.total_rating_count` | proven cumulative demand |
| rating | `product_rating.average_rating_value` | satisfaction / return-risk |
| discount depth | Shopify `compare_at_price` vs `price` | positioning, margin pressure |
| what KAUCHE pushes | `GetHomeContent` time sale, `deals` | merchandising intent |
| best sellers | `kauche_sales_ranking` (needs login) | ground-truth ranking |
| a rival's catalog | `kauche_shop_products(partner_id)` | competitor teardown |

## Score (v1, `kauche/win.py`)

    win_score = reviews_28d * rating_factor
    rating_factor = rating/5         (rating >= 3.8)
                  = 0.5 * rating/5   (rating < 3.8, quality penalty)

Reported alongside: price, discount, rating, reviews_28d, reviews_total, share link.

## Thresholds (fixed BEFORE measuring — issue-log discipline)

A **win candidate** = reviews_28d >= 10 AND rating >= 3.8.
- Proven-but-cooling: high `reviews_total` but low reviews_28d → a validated product whose
  hype passed; good to source if you can refresh the angle.
- New + fast: low total but high 28d → rising; watch 2 weeks before committing.

Validate the proxy: a candidate should also appear/stay in `sales_ranking` (after login).
If it ranks high on reviews but never in sales_ranking, the reviews were campaign-driven
(coin/farm) — downgrade. Log each scan + outcome in `memory/ISSUES.md` when it drives a
real listing decision.

## Caveats / data gaps

- No absolute sales/revenue; ranking is order-only. Review velocity is a proxy, skewed up
  for products in farm/coin campaigns.
- Rate limits: scan samples (time sale / ranking / a few rival shops), never the whole catalog.
- Some time-sale items are app-exclusive → no Shopify price.

## Roadmap

- v2 (after `kauche login`): seed candidates from `sales_ranking`; add competitor density
  via `ListSimilarProducts` (how many shops sell the same item → prefer low competition).
- v3: track scans over time (store snapshots) to compute true velocity and trend.
