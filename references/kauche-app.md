# How the KAUCHE app works (for agents answering user questions)

Sources: Google Play / App Store listings, kauche.com, pages.kauche.com, faq.kauche.com,
seller.kauche.com — all read 2026-11-09. Quote the FAQ URL when a user needs the rule.

## Identity

- App: KAUCHE（カウシェ）- ショッピングアプリ. Android `com.kauche.kauche`, iOS id1527218749.
- Developer: KAUCHE, Inc. (Tokyo). Category Shopping. Play: 4.3★ / 32k reviews / 1M+ installs,
  updated 2026-10-30. App Store: 4.5★ / 150k ratings, v2.164.0, 188 MB, iOS 17+, iPhone only.
  Claimed 8M cumulative downloads.
- Japanese only market. Payment: Apple Pay, credit card, PayPay. "面倒な会員登録なし" —
  guest purchase possible; Apple/Google sign-in recommended; phone verification for some quests.
- Marketplace: each product is sold and shipped by a 販売会社 (the `vendor`). Cancellation /
  return after purchase is **not allowed in principle**; defects → contact the seller with the
  order number (FAQ キャンセルや返品はできますか).

## Three pillars

1. **日替わりセール (daily sale)** — new deals every day (food, daily goods, beauty, appliances,
   訳あり / 在庫処分). On the storefront these are the `shiire-higawari-MMDD` collections.
2. **カウシェファーム (Kauche Farm)** — grow a crop by watering daily; harvest ⇒ a 100%OFF
   coupon for a target product that ships for real. Started via LINE link from the Home banner.
3. **シェア & コイン** — share purchased products; when a friend buys from your share both earn
   coins; posting a review (感想投稿) alone earns coins. Coins → coupons from My Page.
   Coins expire 180 days after the last earn.

Also: **おさんぽ機能** — daily step count (Health Connect / HealthKit) gives farm water and
fertilizer. **カウシェdeポン** — a daily gacha (needs phone verification).

## Farm mechanics (FAQ 作物の育て方 / クエスト)

- Bucket: +0.01 g water per second, holds 30 g, overflow lost; move to the watering can in ≥1 g units.
- Watering can: one tap = 10 g to the crop; needs ≥10 g; cap 999,999 g.
- Fertilizer sets 栄養: 0 ⇒ ×1 growth, 1–44 ⇒ ×1.5, ≥45 ⇒ ×2; each 10 g watered consumes 1 栄養;
  cap 99,999; never expires. Crops never wither.
- Farm day = 04:00–03:59 JST; daily quest caps reset at 04:00; some are per 朝(4–10:59)/昼(11–16:59)/夜(17–3:59).
- Water quests: login, view a product 15 s, watch CM, greet a friend, buy a 💧-marked target
  product, surveys, weekly survey challenge, view an app/service 30 s (iOS).
- Fertilizer quests: login, カウシェdeポン, view a product 30 s, watch CM, water a friend's crop,
  一緒にお買い物クエスト (with ≥11 farm friends), weekly game challenge.
- Friend invite: inviter gets water/fertilizer, invitee gets fertilizer; one reward per phone number;
  not paid once the inviter's daily cap is hit or if the invitee already finished the tutorial.
- Purchase quest: must order while the product is a target; orders paid with the 100%OFF farm
  coupon earn nothing; a time-limited purchase bonus and the quest reward cannot both be claimed.
- Survey / weekly-game rewards may take up to 72 h / 48 h.
- Reviews on Play (2026-09) say growth is slow without buying; purchases give lots of water/fertilizer.

## Harvest coupon (FAQ 対象商品に使える100%OFFクーポン)

- Granted when a crop completes; it is a coupon, not the crop. Valid **30 days**, not reissued,
  not transferable. Use: My Page → クーポン → copy code → 対象商品を見る → 購入 → apply at checkout.
- Price becomes ¥0 but **shipping may still be charged** by region. Cannot be applied or
  cancelled after the order completes. Target products change over time — check `farm-targets`.

## Accounts and coupons

- One account per person; account holds purchase history, coins, coupons. Transfers / logout /
  email change have FAQ articles under アカウント関連.
- Coupon articles (usage, reissue, stacking, transfer, expiry) are under その他 on faq.kauche.com.

## Seller program (seller.kauche.com)

- 初期費用・月額固定費 0 円. 販売手数料 10 % + 決済手数料 3.5 %. 3 steps: 申込 → 審査 → 出品.
- Extra services: in-farm ad slots (新商品閲覧クエスト, click-billed), logistics
  (マルチチャネル運賃 60サイズ 470円〜). Press: news.kauche.com.

## Hostnames (observed)

kauche.com (Firebase landing + share redirect), kauche.myshopify.com (catalog), pages.kauche.com,
faq.kauche.com, seller.kauche.com, about.kauche.com, news.kauche.com, forms.kauche.com /
kauche.fillout.com (forms), api.kauche.com (private app API, Fastly). Not seen: share./app./web.
subdomains, `kauche.page.link`. In-app scheme `kauche://app` appears in the storefront theme.

## Useful official URLs

- https://pages.kauche.com/farm/about-farm — farm overview
- https://faq.kauche.com/作物の育て方について-6518d7ffedb253001cd35a6a
- https://faq.kauche.com/クエストについて-6518d84f0e0ad5001b740570
- https://faq.kauche.com/対象商品に使える100%OFFクーポンについて-6518db0c6ae96f001c1f9b5c
- https://faq.kauche.com/キャンセルや返品はできますか-6152d02b06b39c0023e83248
- https://seller.kauche.com/ , https://about.kauche.com/tos/ , https://about.kauche.com/tokutei/
