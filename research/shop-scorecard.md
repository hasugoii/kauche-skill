# Chấm điểm shop さつまいもん家 vs top — 3 ô đang bán (2026-11-10)

> Shop của anh (partner_id `1bd2d1f6-f8b6-427b-be31-1559e23e5712`) **đang bán cả 3 ô**:
> khoai lang, khoai tây, hành tây (+ hồng 柿 theo mùa, đang hết hàng). Nên đây KHÔNG còn là
> "có nên mở ô mới không" — mà là **chấm điểm & sửa cái đang có**. Điều này **lật lại** kết luận
> "BỎ hành tây / khoai tây" trước đây (xem mục "Sửa kết luận" cuối file).

Nguồn: `kauche_shop_products` (partner_id) + GraphQL tag `partnerID` + review pull từng listing +
win_scan ô じゃがいも/玉ねぎ. Review = xu thưởng → proxy doanh số.

---

## Toàn bộ listing của shop (13 SP)

| Ô | SP | Giá | ★ | Review | Coupon | Ghi chú |
|---|---|---:|---:|---:|---|---|
| 🍠 Khoai lang | mix 5kg | ¥2.320 | 4.4 | 1.394 | 15% | **cờ đầu, #1 ô tươi** |
| 🍠 | 訳あり 5kg (紅はるか) | ¥2.120 | 4.4 | (chung) | 15% | |
| 🍠 | 紅はるか 5kg M | ¥2.820 | 4.3 | 6 | 15% | bản cao cấp mới |
| 🍠 | 訳あり 2kg | ¥1.580 | — | 0 | — | **mới, chưa có review** |
| 🍠 | 訳あり 10kg | ¥3.680 | — | 0 | — | **mới, chưa có review** |
| 🥔 Khoai tây | 訳あり 2kg 北海道 | ¥1.620 | **5.0** | 10 | 15% | sạch tuyệt đối |
| 🥔 | 訳あり 5kg 北海道 | ¥2.620 | — | 0 | 15% | **chưa có review** |
| 🥔 | 訳あり 10kg 北海道 | ¥3.720 | **4.9** | 15 | 15% | bản có review |
| 🥔 | 訳あり 10kg 北海道 | ¥2.720 | — | 0 | 15% | **TRÙNG 10kg** (rẻ hơn ¥1.000, 0 review) |
| 🧅 Hành tây | 北海道 2kg | ¥1.580 | — | **0** | — | **0 review, 1 ảnh, không coupon** |
| 🧅 | 北海道 5kg | ¥2.380 | — | **0** | — | như trên |
| 🧅 | 北海道 10kg | ¥3.280 | — | **0** | — | như trên |
| 🍂 Hồng 柿 | 富有柿 2.5kg | ¥2.291 | 4.5 | 2 | — | hết hàng (hết mùa) |

---

## Bảng điểm (A = mạnh → F = yếu)

| Ô | Giá vs top | Chất lượng (★) | Độ phủ (review) | Listing | Độ khốc liệt ô | **Tổng** |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| 🍠 Khoai lang | B (¥2.1-2.3, hợp lý) | B (4.4) | **A** (1.394, #1) | B | A (ô dễ) | **A– — dẫn đầu, giữ & vá lỗi mốc/thối** |
| 🥔 Khoai tây | C (cao hơn top) | **A+** (4.95, sạch nhất ô) | **D** (25, chìm) | B | B (天地 mạnh vừa) | **B — "ngọc ẩn": chất vô địch, chưa ai thấy** |
| 🧅 Hành tây | **D** (đắt hơn mọi tier) | ? (0 review) | **F** (0) | C– (khô, 1 ảnh, no coupon) | **F** (124k rv @¥980) | **D — yếu nhất, ô khó nhất** |

### Đọc bảng
- **Khoai lang** — đã có plan riêng (`khoailang-shop-plan.md`): giữ ngôi đầu, sửa mốc/thối + phản hồi 24h.
- **Khoai tây = ưu tiên tăng trưởng số 1.** ★4.95 của anh **cao hơn cả 天地の恵み ★4.8** (381 rv) và
  ファームかずと ★4.7 — tức **chất lượng đã vô địch ô này**, chỉ thiếu *người thấy*. Review khen giao
  nhanh, củ sạch đều, và **rất nhiều người mua kèm bằng coupon bắn ra từ khoai lang**. → Đòn bẩy là
  **visibility + giá + gộp SKU trùng**, KHÔNG phải chất lượng. Chi tiết: `listing-khoai-tay.md`.
- **Hành tây = ô khó nhất, đừng đổ lực làm trụ.** Một cụm bán khổng lồ (マイファーマーズ/市川, **124k
  review** ★4.7) đã chốt ¥980/2kg + sẵn 補償. Giá anh cao hơn ở MỌI tier, 0 review, 1 ảnh, không coupon.
  → Sửa listing cho đúng chuẩn + gắn coupon + hạ giá về sát mặt bằng, coi như **hàng kèm giỏ**, đo thử;
  không kỳ vọng tự lên top. Chi tiết: `listing-hanh-tay.md`.

---

## Vị trí shop mình trong từng ô (win_scan top 16, 2026-11-10)

**🥔 Khoai tây** — top hàng củ tươi: 天地の恵み 5kg ¥2.280 ★4.8 (381rv), 10kg ¥3.480 ★4.7 (175rv);
ファームかずと 5kg ¥1.800 ★4.7 (354rv, scan trước). **Shop mình KHÔNG lọt top 16** (25 review → bị chìm).
→ giá mình (5kg ¥2.620 / 10kg ¥3.720) **cao hơn** top, review **ít hơn** → thua kép ở lượt sort.

**🧅 Hành tây** — top: マイファーマーズ/市川 2kg **¥980** (124k rv), 10kg ¥3.180; 一ツ橋 1.7kg ¥1.280
規格外 (6.6k rv); 国華園 10kg ¥2.670 / 5kg ¥1.980. **Shop mình KHÔNG lọt top 16** (0 review).
→ giá mình (2kg ¥1.580 / 5kg ¥2.380 / 10kg ¥3.280) **cao hơn** top ở mọi tier, 0 social proof.

---

## Sửa kết luận (nguyên tắc: sai thì rút công khai)

| Ô | Kết luận trước (file cũ) | Vì sao sai | Sau khi biết shop đang bán |
|---|---|---|---|
| 🥔 Khoai tây | "BỎ — sạch + bị undercut ¥1.800" | Khung sai: tưởng đang cân nhắc **MỞ MỚI**. Thực ra **đang bán, ★4.95** | **GIỮ & ĐẨY** — ngọc ẩn, sửa giá + visibility |
| 🧅 Hành tây | "BỎ — 2kg ¥980 + 124k rv" | Như trên: đang bán rồi (3 listing, 0 review) | **SỬA tối thiểu + đo** — ô khó nhưng đã lỡ bày hàng |

Khung đúng cho cả 3 ô (giống khoai lang): **review & số liệu của shop = tự soi (audit), không phải
đối thủ.** Thứ tự dồn lực: 🍠 khoai lang (giữ đầu) › 🥔 khoai tây (đẩy, dễ ăn nhất vì chất đã vô địch)
› 🧅 hành tây (vá listing, đo, không kỳ vọng).
