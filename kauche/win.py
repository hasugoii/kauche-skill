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
WIN_MIN_REVIEWS = 500   # proven cumulative demand for a "win candidate"
_WINDOW_DAYS = 28
_PAGE_CAP = 10          # ListProductFeedbacks returns ~10 recent reviews per page;
                        # reviews_28d saturates here unless paginated (momentum flag only)


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


def _seed_from_collection(k, handle, limit):
    """Candidate products from a Shopify sale collection (anonymous): already carries
    title, vendor (shop), price, discount and the numeric id -> gid."""
    out = []
    for p in k.collection_products(handle, limit=limit):
        out.append({
            "gid": f"gid://shopify/Product/{p['id']}", "handle": p["handle"],
            "title": p.get("title"), "vendor": p.get("vendor"),
            "price": p.get("price"), "compare_at_price": p.get("compare_at_price"),
            "discount_pct": p.get("discount_pct"),
        })
    return out


def _seed_from_timesale(k, limit):
    out = []
    for item in k.time_sale()[:limit]:
        p = item.get("product", item)
        gid = (p.get("shopify_product_gid") or {}).get("gid")
        if gid:
            out.append({"gid": gid, "handle": p.get("handle")})
    return out


def _seed_from_search(k, query, limit):
    out = []
    for p in k.shop.search(query, limit=limit):
        out.append({"gid": f"gid://shopify/Product/{p['id']}", "handle": p["handle"],
                    "title": p.get("title"), "vendor": p.get("vendor"),
                    "price": p.get("price"), "compare_at_price": p.get("compare_at_price")})
    return out


def win_scan(limit: int = 8, with_price: bool = True, collection: str = None,
             search: str = None, k: Kauche | None = None) -> list:
    """Score products by win_score, best first. Source (pick one):
      search=<keyword>     keyword search (your niche: 'さつまいも', 'iphone ケーブル'...)
      collection=<handle>  a Shopify sale collection (shows competitor vendor)
      default              the home time sale
    Fully anonymous."""
    k = k or Kauche()
    if search:
        seeds = _seed_from_search(k, search, limit)
    elif collection:
        seeds = _seed_from_collection(k, collection, limit)
    else:
        seeds = _seed_from_timesale(k, limit)
    rows = []
    for s in seeds:
        gid, handle = s.get("gid"), s.get("handle")
        if not gid:
            continue
        rating_val, total, velocity, breakdown = None, None, None, None
        try:
            r = k.reviews(gid)
            rating = r.get("product_rating") or {}
            rating_val = rating.get("average_rating_value")
            total = rating.get("total_rating_count")
            breakdown = {s: rating.get(name + "_rating_count")
                         for s, name in [(5, "five"), (4, "four"), (3, "three"), (2, "two"), (1, "one")]}
            velocity = _velocity(r.get("product_feedbacks") or [])
        except (ConnectError, Exception):
            pass
        title, vendor = s.get("title"), s.get("vendor")
        price, cmp, discount = s.get("price"), s.get("compare_at_price"), s.get("discount_pct")
        if with_price and handle and price is None:
            try:
                sp = k.shop.product(handle)
                price, cmp, discount = sp.get("price"), sp.get("compare_at_price"), sp.get("discount_pct")
                title, vendor = sp.get("title"), sp.get("vendor")
            except Exception:
                pass
        rf = 0.0
        if rating_val is not None:
            rf = rating_val / 5.0 if rating_val >= RATING_GATE else 0.5 * rating_val / 5.0
        # Proven, satisfaction-weighted demand. reviews are coin-rewarded on KAUCHE, so
        # total_rating_count tracks lifetime sales. velocity (page-capped) is momentum only.
        score = round((total or 0) * rf)
        rows.append({
            "score": score,
            "win_candidate": bool((total or 0) >= WIN_MIN_REVIEWS and (rating_val or 0) >= RATING_GATE),
            "hot": bool(velocity and velocity >= _PAGE_CAP),  # recent page all within 28d
            "title": title,
            "vendor": vendor,
            "price": price,
            "discount_pct": discount,
            "rating": rating_val,
            "reviews_total": total,            # coin-rewarded on KAUCHE -> best public sales proxy
            "reviews_breakdown": breakdown,    # {5:..,4:..,3:..,2:..,1:..}
            "reviews_28d_min": velocity,  # lower bound (page-capped at ~10)
            "handle": handle,
            "product_gid": gid,
            "share_link": f"https://kauche.com/products/{handle}" if handle else None,
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows
