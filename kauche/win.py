"""Winning-product research for KAUCHE (competitor + product discovery).

The useful signal on KAUCHE: reviews are rewarded with coins, so review count tracks
real purchases closely — a better sales proxy than most marketplaces. `win_scan` scores
products KAUCHE is actively pushing (home time sale) by:

    win_score = review_velocity_28d * rating_factor

    review_velocity_28d  reviews posted in the last 28 days (recent demand)
    rating_factor        avg_rating/5, halved when rating < RATING_GATE (quality gate)

It also reports lifetime `total_rating_count` (cumulative demand) and the Shopify
discount depth. Prices/discount come from the public storefront (best-effort; some
time-sale items are app-exclusive and won't resolve).

Thresholds (set before measuring — see references/win-method.md):
    WIN_VELOCITY >= 10 reviews/4wk, RATING_GATE >= 3.8  -> a "win candidate".

v1 is anonymous: time-sale seed. v2 (after `kauche login`) will seed from
sales_ranking and add competitor-density via similar products. Keep scans small
(rate limits); default 8 products.
"""
from __future__ import annotations

import datetime as dt

from .client import Kauche
from .connect import ConnectError

RATING_GATE = 3.8
WIN_VELOCITY = 10
_WINDOW_DAYS = 28


def _velocity(feedbacks, days=_WINDOW_DAYS):
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    n = 0
    for fb in feedbacks:
        ts = (fb.get("user_post") or {}).get("post_time")
        if not ts:
            continue
        try:
            t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if t >= cutoff:
            n += 1
    return n


def win_scan(limit: int = 8, with_price: bool = True, k: Kauche | None = None) -> list:
    """Score the current time-sale products by win_score, best first."""
    k = k or Kauche()
    rows = []
    for item in k.time_sale()[:limit]:
        p = item.get("product", item)
        gidobj = p.get("shopify_product_gid") or {}
        gid = gidobj.get("gid")
        handle = p.get("handle")
        if not gid:
            continue
        rating_val, total, velocity = None, None, None
        try:
            r = k.reviews(gid)
            rating = r.get("product_rating") or {}
            rating_val = rating.get("average_rating_value")
            total = rating.get("total_rating_count")
            velocity = _velocity(r.get("product_feedbacks") or [])
        except (ConnectError, Exception):
            pass
        price = cmp = discount = title = vendor = None
        if with_price and handle:
            try:
                sp = k.shop.product(handle)
                price, cmp, discount = sp.get("price"), sp.get("compare_at_price"), sp.get("discount_pct")
                title, vendor = sp.get("title"), sp.get("vendor")
            except Exception:
                pass
        rf = 0.0
        if rating_val is not None:
            rf = rating_val / 5.0 if rating_val >= RATING_GATE else 0.5 * rating_val / 5.0
        score = round((velocity or 0) * rf, 2)
        rows.append({
            "score": score,
            "win_candidate": bool(velocity and velocity >= WIN_VELOCITY and (rating_val or 0) >= RATING_GATE),
            "title": title,
            "vendor": vendor,
            "price": price,
            "discount_pct": discount,
            "rating": rating_val,
            "reviews_total": total,
            "reviews_28d": velocity,
            "handle": handle,
            "product_gid": gid,
            "share_link": f"https://kauche.com/products/{handle}" if handle else None,
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows
