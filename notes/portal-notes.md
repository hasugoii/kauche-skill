# Portal notes — traps found while building this skill (append yours)

2026-11-09 (initial reverse-engineering session)

- Play Store page is client-rendered: plain HTTP fetch returns only the title. Use a browser.
- `www.kauche.com` does not resolve. `kauche.com` is Firebase Hosting; any `*.json` there is a
  Firebase 404 page, not Shopify.
- The real catalog host was found because `https://kauche.com/products/1` 301s to
  `https://kauche.myshopify.com/products/1`. `robots.txt` on kauche.com disallows the usual
  Shopify paths (`/collections/`, `/products/`, `/checkouts/`, plus app-only `/farm/`, `/gacha/`,
  `/groups/`, `/coupons/`, `/users/`, `/tab/`, `/link/`, `/partners/`).
- Rate limit trips fast (≈8–10 quick requests) and stays for minutes. The first symptom on HTML
  routes is a body that just says `local_rate_limited`; JSON routes answer `TOO_MANY_REQUESTS`.
  Even `products.json?page=1` then returns `{"products":[]}` with 429 — an empty list is not
  "no products"; check the status code.
- `search/suggest.json` → `417 Unsupported buyer locale` regardless of `Accept-Language`.
  Predictive search seems disabled for this shop's locale; not fixable client-side so far.
- Product pages render with the Shopify "Taste" theme but the buy button is 「アプリで購入」 and the
  cart drawer says 「カウシェアプリで続ける」: web checkout is intentionally disabled.
- Collection `products_count` values are huge (e.g. 3,142,930) — treat as "pool", never paginate to
  the end.
- Collections with `[使っていない]` in the title are abandoned by staff; skip them.
