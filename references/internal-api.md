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
