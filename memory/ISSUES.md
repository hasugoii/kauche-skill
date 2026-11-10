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
