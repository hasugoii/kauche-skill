# Phân tích TOÀN BỘ review さつまいもん家 (khoai lang) — nỗi đau + điều khen

Ngày: 2026-11-10. Nguồn: kéo hết **1.378/1.393 review** (listing mix 5kg ¥2.320, product_id
9030507036840) qua RPC, đọc đầy đủ chữ. Script: `scratchpad/fullpull.py` + `analyze.py`.

## 0. Tổng quan phân bố

| Sao | Số lượng | % |
|---|---:|---:|
| ★5 | 928 | 67% |
| ★4 | 291 | 21% |
| ★3 | 98 | 7% |
| ★2 | 31 | 2% |
| ★1 | 30 | 2% |

→ ★ trung bình 4.4. **1-2★ chỉ 4,4%** nhưng nội dung rất tập trung. Đây là hàng **訳あり** (loại
xô, "hàng lỗi giá rẻ"), nên khách tự nhận lỗi là **"運" (hên xui)** — cùng một sản phẩm, người khen
nức nở, người vứt nửa thùng. **Thắng = biến hên-xui thành chắc chắn.**

---

## 1. NỖI ĐAU — tần suất từ khóa trong 61 review 1-2★

| Nỗi đau | Số review | % trong 1-2★ |
|---|---:|---:|
| 🦠 Mốc (カビ) | 14 | 23% |
| 🩹 Trầy/dập/thâm (傷・痛み) | 12 | 20% |
| 🤢 Thối (腐) | 11 | 18% |
| 📦 Đóng gói/hộp (梱包・箱 ướt) | 7 | 12% |
| 🗑️ Không ăn được/phải vứt | 6 | 10% |
| 💧 Nhũn (ブヨブヨ/柔) | 4 | 7% |
| 🌱 Mọc mầm sớm (芽) | 3 | 5% |
| 🟤 Ruột nâu/đen (茶色・黒) | 2 | 3% |
| 📏 Quá nhỏ/mảnh | 2 | 3% |
| 🐛 Sâu/bị gặm | 2 | 3% |

**Gộp lại thành 6 nhóm (đọc nguyên văn):**

1. **Mốc + thối + nhũn (chiếm ~một nửa).** "半分カビと腐れで捨てた" (nửa thùng mốc+thối phải vứt),
   "1本完全に腐っていてブヨブヨ", mốc ở chỗ cắt đầu củ (切り口), hộp đáy ướt → 1 củ thối chảy nước lan
   sang củ khác, **mốc trong chưa đầy 1 tuần** (1週間も経たず下はぐにゃぐにゃ・カビ).
2. **Cỡ củ thất thường.** Hai cực đều bị chê: **quá to không làm 焼き芋 được** ("顔よりデカイ", "大きすぎて
   切らないと無理", "焼き芋サイズがない") và **quá nhỏ/mảnh** ("痩せ細った", "手でパキッと折れる細長").
3. **Giống không rõ (品種不明).** Lặp nhiều: "品種不明でした", "栗かぐや希望だったが紅はるか届いた". Khách
   bực vì không biết mình nhận giống gì.
4. **Vị kém.** Nhạt/khô ("甘くない", "パサパサ"), nhiều xơ ("繊維が多く噛みきれない"), đắng/aku ("アク",
   "苦い"), rỗng ruột ("スカスカ", "スの通った").
5. **Mọc mầm sớm (芽)** → rút dinh dưỡng, vị giảm.
6. **Shop KHÔNG trả lời khiếu nại.** "問い合わせても返信すら返ってこない" (lặp ≥3 lần). Đây là **lỗ hổng
   vận hành** — không phải sản phẩm.

---

## 2. ĐIỀU KHEN — tần suất từ khóa trong 1.219 review 4-5★ (= baseline BẮT BUỘC phải làm được)

| Điều khách khen | Số review | % trong 4-5★ |
|---|---:|---:|
| 😋 Ngon (美味しい) | 610 | 50% |
| 🍠 To/đẹp (大き・立派) | 523 | 43% |
| 🍯 Ngọt (甘い) | 396 | 33% |
| 🔥 Hợp làm 焼き芋 | 329 | 27% |
| 🚚 Giao nhanh (早い) | 255 | 21% |
| 🔁 Mua lại (リピート) | 248 | 20% |
| 📦 Nhiều/đầy (量・たっぷり) | 230 | 19% |
| 🍮 Dẻo/bở ngọt (しっとり/ねっとり/ホクホク) | 194 | 16% |
| 🎁 Đa dạng giống (品種・色々) | 179 | 15% |
| ✨ Đóng gói sạch/cẩn thận (丁寧・きれい) | 54 | 4% |
| 👶 Trẻ con/cháu thích | 39 | 3% |

**Baseline khách coi là mặc định (không làm được = mất sao, dù không mốc):**

1. **Ngon + ngọt** là #1 (50% + 33%). Vị phải thật sự ngọt → chọn 紅はるか + **追熟 (ủ cho lên mật)**.
2. **To VÀ nhiều** (43% + 19%) — khách sướng vì cảm giác "どっさり", "手のひらより大きい". **Nhưng** (mục 1.2)
   to-quá-cỡ lại là nỗi đau → sweet spot = **nhiều + cỡ dùng được, đủ củ size 焼き芋**, không phải toàn
   củ khổng lồ.
3. **Giao nhanh** (21%) — khen rất nhiều "昨日頼んだのに今日きた". Phải ship nhanh (hôm sau / 2 ngày).
4. **Hợp làm 焼き芋** (27%) — đa số mua để nướng. Cỡ + độ ngọt + kết cấu phải nướng ngon.
5. **Dẻo ngọt** (16%) しっとり/ねっとり — kết cấu mật.
6. **Trạng thái sạch, KHÔNG hư** vừa là baseline vừa là *delight*: nhiều 5★ khen riêng "傷んでる物が無く
   状態よくて大満足" — **không hư = khách phát cuồng**, đúng chỗ đối thủ hên xui.
7. **Phản hồi nhanh cứu được sao:** một 5★ dù có củ hư vẫn cho 5★ vì "問い合わせのレスポンスが早く満足" →
   trái ngược đối thủ thường im lặng.

---

## 3. Hệ quả cho listing của mình (định vị "anti-hên-xui")

Đối thủ bán **訳あり = xổ số**. Mình thắng bằng cách **bỏ yếu tố may rủi** — vừa tránh nỗi đau, vừa
đảm bảo mọi điều khách khen:

| Trục | Nỗi đau cần tránh | Điều khen phải làm được | Cách làm |
|---|---|---|---|
| Tình trạng | mốc/thối/nhũn | "không hư = đại mãn nguyện" | 選別 + ủ thoáng + **bảo hành đổi/hoàn** |
| Cỡ củ | to vô dụng / mảnh | cỡ 焼き芋 chuẩn, nhiều | **選別 theo size (M)** + ghi rõ khoảng cỡ |
| Giống | 品種不明 | thích "biết giống mình nhận" | **ghi rõ giống (紅はるか)** trên bao |
| Vị | nhạt/khô/xơ/aku | ngọt, dẻo, nướng ngon | 紅はるか + **追熟 lên mật** |
| Giao | hộp ướt | giao nhanh (khen nhiều) | ship ≤2 ngày + chống ẩm |
| Hỗ trợ | im lặng khi khiếu nại | "phản hồi nhanh → vẫn 5★" | **trả lời + đổi trong 24h** |
| Giá | — | rẻ/cospa so với siêu thị | giữ giá hợp lý (xem listing) |

→ 3 điểm BỔ SUNG so với listing cũ (vốn mới chỉ nhắm mốc): **(a) chọn-lọc theo CỠ (焼き芋 chuẩn,
không toàn củ khổng lồ), (b) GHI RÕ GIỐNG, (c) GIAO NHANH + PHẢN HỒI 24h.** Đây đều là điều khách
đã khen/chê sẵn, đối thủ làm hên xui — mình làm chắc chắn thì thắng.
