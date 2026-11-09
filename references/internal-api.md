# KAUCHE internal app API (api.kauche.com) — reverse-engineering reference

Reverse-engineered from the Android APK **v2.164.0 (versionCode 31207)**, 2026-11-09.
Native Kotlin app (R8-obfuscated), Apollo + Shopify Mobile Buy SDK + a Connect-RPC
backend. This documents the backend the app itself talks to. Read-only use; checkout
and writes stay in the app.

## Backends

| Plane | URL | Auth | Protocol | Use |
|---|---|---|---|---|
| **Kauche customer API** | `https://api.kauche.com/api/customer/v1/<Method>` | `Authorization: Bearer <Firebase idToken>` | Connect-RPC, JSON | reviews, ranking, time sale, categories, shops, recommendations |
| **Kauche account API** | `https://api.kauche.com/api/account/v1/<Method>` | same | Connect-RPC | LINE/email login, demographics |
| **Shopify Storefront** | `https://api.kauche.com/api/2026-04/graphql` (and open `https://kauche.myshopify.com`) | `X-Shopify-Storefront-Access-Token` (token from Launch) / none for myshopify JSON | GraphQL / REST | catalog, prices, product detail, collections |
| Farm/walk | `https://farm.kauche.com`, `.../walk` | Firebase | — | farm game, step rewards (not covered here) |

The app fetches `shopDomain` + `storefrontAccessToken` at startup from a **Launch**
RPC (protobuf `LaunchResponse`), then talks to Shopify with the Mobile Buy SDK
(headers: `X-Shopify-Storefront-Access-Token`, `X-SDK-Version: 2026.4.0`,
`User-Agent: Mobile Buy SDK Android/2026.4.0/<pkg>`). Products are Shopify products;
the app references them by `shopify_product_gid` = `gid://shopify/Product/<id>`.

## Auth (Firebase, project `x-asia-kauche-prod`)

- Web API key (client identifier, in the APK): `AIzaSyCMT60jygkdhgCKGgoWHq6HiJP8ZVsx-6U`
- App ID: `1:283378856219:android:b75fd1b919e81735ab23be`
- The app allows shopping without signup, so it uses **anonymous** Firebase auth.
  Reproduce it: `POST https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=<KEY>`
  with `{"returnSecureToken":true}` → `idToken`. Refresh via securetoken.googleapis.com.
- Send `Authorization: Bearer <idToken>` to api.kauche.com. (`kauche/auth.py` does this.)
- **App Check is NOT enforced** on the customer API (verified: calls succeed without
  an `X-Firebase-AppCheck` header). The app has App Check wired for Firebase SDKs and
  Play Integrity for the walk/step feature only.

## Connect-RPC shape

- POST `https://api.kauche.com/api/customer/v1/<Method>`, `Content-Type: application/json`,
  `Accept: application/json`. Body = JSON of the protobuf request message, **snake_case**.
- Some idempotent reads are also exposed over GET (e.g. `customer/v1/coupons`,
  `customer/v1/product_search_settings`, `customer/v1/partners/{id}`).
- Errors are Connect/gRPC envelopes: `{"code":N,"message":"...","details":[]}`.
  Common: 3 InvalidArgument (bad/missing field — message sometimes names the field and
  its validation rule), 13 Internal (often: method needs a signed-in non-anonymous user,
  or the product/entity is unavailable), 7 PermissionDenied, 404 Not Found (deprecated
  method), 500 carries code 13.

## Verified anonymously (200 on 2026-11-09)

| Method | Body | Returns |
|---|---|---|
| `customer/v1/GetHomeContent` | `{}` | `time_sale_section.time_sale_products[].product{id,handle,shopify_product_gid,has_farm_*}` + other sections |
| `customer/v1/ListProductFeedbacks` | `{"shopify_product_gid":{"gid":"gid://shopify/Product/<id>"},"page_token":""}` | `product_feedbacks[]` (reviews: `user_post{message,image_urls,product_rating_value,post_time,owner_user_profile}`), `product_rating{average_rating_value,total_rating_count,five_rating_count..one_rating_count}`, `next_page_token` |
| `customer/v1/ListProductCategories` | `{}` | `product_categories[]{id,name,kind}` |
| `customer/v1/product_search_settings` (GET) | — | recommended search terms, filter settings |
| `customer/v1/coupons` (GET) | — | `coupons[]{id,code,value,value_kind,title,...}` |
| `customer/v1/launch` | `{os_type:2,os_version,app_name,app_version,bundle_number,device_model,device_uuid,locale}` (snake_case; only `os_type` mattered in testing) | `{shopify:{shop_domain:"kauche.myshopify.com", storefront_access_token:"<32hex>", locale}, app_update, user_profile_status}` |

**`launch` is the key to the catalog.** Its `storefront_access_token` is a public Shopify
Storefront token (meant to ship in the client). With it, catalog/search/product go through
the **Storefront GraphQL API** `https://kauche.myshopify.com/api/2026-04/graphql`
(`X-Shopify-Storefront-Access-Token` header) — a generous per-token cost budget, **not**
the ~10 req/min per-IP anti-bot limit on the public website. This is exactly how the app
works; `kauche/shopify.py` fetches the token via `launch` (cached 1h) and uses GraphQL as
the primary path, falling back to website scraping only if `launch`/GraphQL fails. Don't
hardcode the token — fetch it live, it can rotate. Useful GraphQL roots (2026-04):
`search(query:,types:PRODUCT,first:)` (best keyword relevance + `vendor`), `product(handle:)`,
`collection(handle:){products(first:)}`.

## Mapped from the APK (fields known; may need a real user)

Request field schemas were extracted from the decompiled protobuf messages
(`*_FIELD_NUMBER` constants + `newMessageInfo` type info). Field numbers shown.

- `customer/v1/GetProduct` — `{encoded_product_id? #1, product_handle? #2, shopify_product_gid? #3}`.
  Response `{product #1, product_rating #2, compare_at_price_label #3, group_buying_kind #4,
  user_product_shipping_price #5, user_favorite #6, bonus_coin_info #8, has_product_feedbacks #10,
  new_user_discount #11, coupon_label #12}`. **Returned code 13 for anonymous users** — use the
  Shopify storefront for product detail and `ListProductFeedbacks` for ratings.
- `customer/v1/ListProductsBySalesRanking` — `{no_of_products #1 (1..200), page_token #2}`. (code 13 for anon.)
- `customer/v1/ListProductsByNewArrival` — `{no_of_products #1 (1..200), page_token #2}`.
- `customer/v1/ListProductsByPartner` — `{partner_id #1, limit #2, page_token #3}` (a shop's products).
- `customer/v1/partners/{partner_id}` (GET) — shop/seller detail. `partner_id` is the
  UUID seen as `partnerID:<uuid>` on storefront product tags.
- `customer/v1/ListTimeSaleProducts` — `{page_token #1}` (home time sale is easier via GetHomeContent).
- `customer/v1/ListPredictedProducts` — `{page_token #1, scene_name #2}`; resp `{predicted_products #1,
  next_page_token #2, predict_request_id #3, fallback_collection_gid #4}`.
- `customer/v1/SearchProductsByProductPurchaseQuest` — `{search_query #1, quest_type #2, page_token #3}`
  (text search, farm-quest-scoped).
- `customer/v1/products` (POST) — batch product lookup `{list_products:[{product_handle|product_id|shopify_product_gid}]}`.

Full list of all 157 endpoints: `kauche-endpoints.txt`.

## Product object (Shopify + Kauche)

Catalog data (title, price, `compare_at_price`, variants, images, description, vendor,
tags with `categoryID/partnerID/productCode`) comes from Shopify — see
`storefront-api.md`. Kauche overlays rating, coupons, farm-target flags, shipping and
feedback on top via the customer API. Prices are JPY, tax included.

## How this was obtained

APK (APKPure XAPK) → unzip → `jadx` decompile of the base dex → grep for
`com.kauche.core.network` Retrofit interfaces (endpoint paths), `ProtoConverterFactory`
(protobuf), `AuthorizationTokenInterceptor` (Bearer), `SetupShopifyClientUseCase`
(Shopify SDK), and `*_FIELD_NUMBER` (message fields). Live probe (anonymous token)
confirmed auth, absence of App Check, Connect-JSON behavior, and response shapes.
See `../notes/portal-notes.md`.

## Signed-in sessions (login)

Endpoints that return `code 13` for anonymous users need a real Firebase user. The app
signs in with Google, LINE or phone; all produce a Firebase ID token used as
`Authorization: Bearer`. The library (`kauche/account.py`) lets the account owner
establish such a session without Claude handling a password — you bring a credential you
obtained yourself and it is exchanged for a Firebase token via the standard Identity
Toolkit REST API, then persisted (refresh token) and auto-refreshed.

Credential sources (`AccountSession.from_*` / `kauche login`):
- `--refresh-token <rt>` — universal: a Firebase refresh token from your own signed-in
  session. Refreshed via `securetoken.googleapis.com` indefinitely.
- `--custom-token <ct>` — `accounts:signInWithCustomToken`. The LINE flow yields one.
- `--google-id-token <idt>` — `accounts:signInWithIdp`, providerId `google.com`.
- `--apple-id-token <idt>` — same, providerId `apple.com`.

Verified 2026-11-09: the signInWithCustomToken / signInWithIdp / securetoken request
shapes are correct (bogus credentials are rejected with `INVALID_CUSTOM_TOKEN` /
`INVALID_IDP_RESPONSE`, i.e. the plumbing reaches Firebase auth). Issuing a real token
needs your own credential; privileged KAUCHE endpoints were not exercised with a real
account (none was created).

### LINE login flow (from the app)

1. `account/v1/StartLineLogin` `{channel_id, device_uuid}` → `{nonce_id, nonce, channel_id}`.
2. You authorize in LINE (LINE SDK/app) using `channel_id` + `nonce`; LINE returns an
   OIDC `id_token` bound to that nonce.
3. `account/v1/CompleteLineLogin` `{nonce_id, id_token}` → `{firebase_custom_token}`.
4. `AccountSession.from_custom_token(firebase_custom_token)`.

Helpers: `KaucheAPI.start_line_login`, `KaucheAPI.complete_line_login`.

### Provisioning the KAUCHE customer record

After a real sign-in, `customer/v1/CompleteSignIn` provisions your KAUCHE customer
profile (needed by some endpoints). `kauche login --signup` runs it. This is a write
that creates your profile — run it yourself; the library does not do it unprompted.

Phone auth (Firebase PhoneAuthProvider) needs reCAPTCHA/Play Integrity and is not
reproducible headlessly.

### Browser login (easiest)

`kauche login` (no args) runs a one-shot local web server, opens a page in your browser
that signs you into the KAUCHE Firebase project with Google or Apple via the Firebase JS
SDK (`signInWithPopup`), and captures the resulting idToken + refreshToken back into the
AccountSession automatically. Works because `http://localhost` is a default authorized
domain on Firebase projects. Implementation: `kauche/weblogin.py`. Firebase web config is
embedded there (apiKey/authDomain/projectId from the APK). If a project disabled the
localhost authorized domain you get `auth/unauthorized-domain` — then use
`--refresh-token` / `--google-id-token`. LINE has no Firebase popup; use its flow above.

### Token lifecycle

- A signed-in session stores `{id_token, refresh_token, expires_at, email}` in
  `~/.cache/kauche-api/account.json` (chmod 600). The token is never printed.
- `AccountSession.id_token()` returns a valid token, refreshing via securetoken when
  expired. If the refresh token itself is invalid/revoked it clears the session and raises
  `SessionExpired`; with no session it raises `LoginRequired`. Both mean: prompt the user
  to run `kauche login`. The CLI maps these to exit code 2 and an actionable message, or,
  with `--auto-login`, re-opens the browser login and retries.
