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

2026-11-09 (internal API reverse-engineering, APK v2.164.0)

- APK sourced as APKPure XAPK (mirrors block curl: APKPure Cloudflare Turnstile, apkcombo/apkmonk NXDOMAIN in sandbox; user downloaded via browser).
- Native Kotlin app, R8-obfuscated (classes -> defpackage/xx.java). `jadx --no-res` on the 115MB base dex = 76k java files. Retrofit interfaces (com.kauche.core.network) KEEP @POST("customer/v1/...") path strings and *_FIELD_NUMBER constants even under obfuscation -> that's how endpoints + field names were recovered.
- `libsigner.so` is the Adjust SDK signer, NOT a Kauche request signer. No native request signing.
- Backend is Connect-RPC (connectrpc): app uses ProtoConverterFactory (protobuf) but the server content-negotiates and returns JSON when Accept: application/json. So you can call everything with JSON bodies (snake_case) and read JSON responses. Error envelope {"code","message","details"}.
- Auth: Firebase anonymous (project x-asia-kauche-prod, key in resources.arsc). signUp with the API key -> idToken -> Authorization: Bearer. App Check NOT enforced on customer API (only Play Integrity on the walk/step feature).
- Products are Shopify products; app refers by shopify_product_gid (gid://shopify/Product/<id>). shopDomain + storefrontAccessToken come from the Launch RPC (protobuf LaunchResponse) at startup.
- Validation trick for discovering field names: send a wrong value; code 3 messages sometimes name "XxxRequest.FieldName" and the rule (e.g. NoOfProducts range [1,200]). A field that passes validation but 500s (code 13) means the JSON key is correct but the method needs more context / a real user.
- Anonymous works for: GetHomeContent, ListProductFeedbacks, ListProductCategories, product_search_settings, coupons. Returns code 13 for anon: GetProduct, ListProductsBySalesRanking, ListProductsByNewArrival (need a signed-in user).
- Some time-sale products are app-exclusive: 404 on the public Shopify storefront.

2026-11-09 (login/account auth)

- Firebase providers in app: Google (signInWithIdp google.com), LINE (custom-token), phone (reCAPTCHA, not headless), anonymous.
- LINE: account/v1/StartLineLogin{channel_id,device_uuid}->{nonce_id,nonce,channel_id}; user does LINE OIDC with nonce; account/v1/CompleteLineLogin{nonce_id,id_token}->{firebase_custom_token}; Firebase signInWithCustomToken.
- account/v1 is JSON (KotlinSerialization), same host api.kauche.com/api. customer/v1 is protobuf-but-JSON-negotiable.
- customer/v1/CompleteSignIn provisions the KAUCHE customer profile for the firebase uid (req type x53 had no simple scalar fields; likely nested/empty). Likely why anon gets code 13 on ranking/GetProduct.
- Library approach: never handle user's password; accept refresh-token/custom-token/google-id-token/apple-id-token and persist refresh token (securetoken). Verified request shapes against Firebase with bogus creds (INVALID_CUSTOM_TOKEN / INVALID_IDP_RESPONSE). Did NOT create a real account.

2026-11-09 (browser login)

- Full Firebase web config from resources.arsc: apiKey AIzaSyCMT60jygkdhgCKGgoWHq6HiJP8ZVsx-6U, authDomain x-asia-kauche-prod.firebaseapp.com, projectId x-asia-kauche-prod, senderId 283378856219, bucket x-asia-kauche-prod.appspot.com, web OAuth client 283378856219-6i7lsqu39dc3cbb8feg9ic4sjrk6vglh.apps.googleusercontent.com.
- Browser-login = local http server on 127.0.0.1 serving a Firebase JS page; signInWithPopup(Google/Apple) from localhost (a default Firebase authorized domain), page POSTs idToken+refreshToken back to /token. Verified server/page/callback/persist locally with a simulated callback; the Google popup itself needs a real human login (not testable here).
