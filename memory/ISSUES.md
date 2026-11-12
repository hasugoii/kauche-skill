# ISSUES — nhật ký thay đổi chờ đo

Mỗi thay đổi có tác động thật (giá, listing, bid, quy cách…) = một issue mở, **chỉ đóng khi đã đo
xong**. Ngưỡng thành công đặt **trước** khi biết kết quả. Khi đóng → chuyển bài học sang
`memory/DECISIONS.md`. Xem skill `issue-log` để biết quy trình.

Trạng thái: 🟡 chờ áp dụng · 🟢 đang đo · ✅ đã đóng · ⚪ huỷ (bị nhiễu)

---

## 🟡 [khoai-lang / さつまいもん家] Cải thiện vận hành + listing để kéo ★ và giảm 1-2★

Chi tiết việc làm: `research/khoailang-shop-plan.md`. Phân tích gốc: `research/reviews-satsumaimonya.md`.

### Sẽ đổi
- **Vận hành:** (1) chống mốc/thối (loại củ chớm hỏng, bọc giấy từng củ, lót chống ẩm đáy hộp, chỗ
  cắt để lành da, giao nhanh mùa nóng); (2) phản hồi khiếu nại ≤24h + đổi/hoàn cho mốc/thối;
  (3) bớt củ khổng lồ, đảm bảo đủ củ cỡ 焼き芋; (4) ghi rõ giống 紅はるか; (5) xoay vòng tồn chống mầm.
- **Listing:** viết lại tiêu đề + mô tả + ảnh (品種明記, 焼き芋サイズ中心, cam kết 傷み交換, 丁寧梱包) —
  xem PHẦN B của plan.

### Vì sao
Phân tích TOÀN BỘ 1.378 review của chính shop: **~một nửa review 1-2★ là mốc/thối/nhũn** (sửa được
bằng đóng gói, không tốn tiền sản phẩm), và nhiều 1★ do **shop không trả lời khiếu nại**. Review =
doanh số trên Kauche → kéo ★ lên + giảm 1-2★ trực tiếp ra đơn.

### Trạng thái trước khi đổi (mốc gốc — 2026-11-10, từ aggregate)
- ★ trung bình: **4.4**
- Tổng review: **1.393** (5/4/3/2/1 = 940/293/99/31/30)
- **1-2★: 61 review = 4,4%** · 3★: 99 = 7,1%
- Cơ cấu nỗi đau trong 61 review 1-2★: mốc 23% · dập/trầy 20% · thối 18% · đóng gói 12% ·
  phải vứt 10% · nhũn 7% · mầm 5%
- Tốc độ review: _(điền từ dashboard shop — số review/tuần hiện tại, CHƯA có)_
- Biên hiện tại: _(điền)_

### Đo lúc nào, đo cái gì
- **Ngày áp dụng:** _______ (điền khi bắt đầu đổi — đây là mốc t=0)
- **Ngày đo:** áp dụng + 14 đến 21 ngày
- Chỉ số quyết định: tỉ lệ 1-2★ (của review MỚI sau mốc) + ★ trung bình của review mới + tốc độ review/tuần
- **Ngưỡng thành công (đặt trước):**
  - Review mới sau mốc: **0 review nhắc mốc/thối** trong 14 ngày đầu, VÀ
  - ★ trung bình review mới ≥ **4.6** (so với 4.4 nền), VÀ
  - tốc độ review/tuần không giảm (giữ hoặc tăng).
  - Đạt cả 3 → cải thiện có tác dụng → giữ + nhân rộng cách đóng gói.
  - Nếu vẫn còn review mốc/thối → khâu đóng gói/tuyển chọn chưa đủ, soát lại trước khi kết luận.

Label: `listing` `fresh-triage` `kauche` `khoai-lang`

---

## 🟡 [khoai-tay / さつまいもん家] Đẩy visibility khoai tây (ngọc ẩn ★4.95)

Chi tiết: `research/listing-khoai-tay.md`. Chấm điểm: `research/shop-scorecard.md`.

### Sẽ đổi
(1) Gộp 2 SKU 10kg trùng → giữ bản có 15 review, hạ ¥3.720→¥3.180, ẩn bản ¥2.720 0rv.
(2) Hạ 5kg ¥2.620→¥2.280 (**chỉ sau khi kiểm giá vốn + ship không lỗ**).
(3) Đẩy coupon chéo từ khoai lang (kênh đã chạy). (4) Vá listing: ghi giống, ghi nông trại, +送料無料, +ảnh.

### Vì sao
★4.95 (25rv) **cao hơn 天地 ★4.8 (381rv)** → chất đã vô địch, chỉ thiếu người thấy (không lọt top 16).
Review xác nhận khách mua kèm qua coupon khoai lang → đòn bẩy rẻ nhất.

### Trạng thái trước khi đổi (mốc gốc — 2026-11-10)
- Tổng review khoai tây: **25** (2kg: 10 ★5.0 · 10kg-A: 15 ★4.9 · 5kg: 0 · 10kg-B: 0)
- Không lọt top 16 ô じゃがいも. Giá: 2kg ¥1.620 · 5kg ¥2.620 · 10kg ¥3.720/¥2.720
- Giá vốn + ship/đơn: _(điền — CẦN để quyết có hạ 5kg được không)_

### Đo lúc nào, đo cái gì
- **Ngày áp dụng:** _______ (t=0)  ·  **Ngày đo:** +21 ngày
- Ngưỡng ĐẠT (đặt trước): review mới **+15 (→~40)** VÀ ≥1 listing lọt **top ~10** VÀ ★ giữ **≥4.7**.
- Trung bình: +5–14 review, chưa top → giữ, soi lại. Thất bại: <5 review mới hoặc ★<4.5 → coi là hàng kèm.

Label: `listing` `price` `kauche` `khoai-tay`

---

## 🟡 [hanh-tay / さつまいもん家] Cứu listing hành tây 0 review (mức tối thiểu)

Chi tiết: `research/listing-hanh-tay.md`. Chấm điểm: `research/shop-scorecard.md`.

### Sẽ đổi
(1) Gắn coupon 15%. (2) Hạ giá tier không lỗ: 5kg ¥2.380→¥1.980, 10kg ¥3.280→¥2.680 (2kg để nguyên/bỏ,
KHÔNG đua đáy ¥980). (3) Viết lại listing (bỏ câu từ chối giao khỏi đầu, +hook, +送料無料, +3-4 ảnh),
nhấn **北海道産 + giao nhanh** (đối thủ giao tới 10営業日). KHÔNG đổ lực làm trụ.

### Vì sao
Cả 3 listing **0 review**, giá cao hơn top mọi tier, không coupon, 1 ảnh, mô tả khô. Hàng đã bày nên
sửa cho sống + đo; nhưng cụm 124k rv @¥980 gần như bất khả xâm phạm → chỉ làm phần rẻ + hạ giá vừa phải.

### Trạng thái trước khi đổi (mốc gốc — 2026-11-10)
- Review: **0 / 0 / 0** (2kg ¥1.580 · 5kg ¥2.380 · 10kg ¥3.280). Không lọt top 16 ô 玉ねぎ.

### Đo lúc nào, đo cái gì
- **Ngày áp dụng:** _______ (t=0)  ·  **Ngày đo:** +21 ngày
- Có cửa: ≥8 review mới (gộp 3 tier) VÀ ★≥4.5. Hàng kèm: 1–7. **Bỏ đầu tư:** 0 review dù đã coupon+giá sát.

Label: `listing` `price` `kauche` `hanh-tay`
