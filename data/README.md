# Dữ liệu của dự án

## Nguồn và tính bất biến

- `raw/energydata_complete.csv`: bản sao nguyên trạng của UCI Appliances Energy Prediction do nhóm cung cấp.
- SHA-256 của bản raw: `2820BF712AD0275CB18B85A05250926100D8E65EBB9F4D2D016CA91EA152A25D`.
- Không sửa trực tiếp dữ liệu trong `raw/`.
- `.gitattributes` giữ xuống dòng CRLF của tệp raw khi checkout trên mọi hệ điều hành để checksum trên không đổi.

## Đầu ra tiền xử lý

Các tệp dưới đây được tạo lại hoàn toàn khi chạy `notebooks/01_data_preparation.ipynb`:

- `processed/energy_forecasting_h1_full.csv`: toàn bộ các quan sát có nhãn dự báo 1 giờ.
- `processed/energy_forecasting_h1_train.csv`, `..._validation.csv`, `..._test.csv`: chia theo thời gian với ranh giới danh nghĩa 70%/10%/20%, rồi loại 6 dòng cuối train và 6 dòng cuối validation để tránh nhãn lấn sang tập kế tiếp.
- `processed/data_quality_summary.json`: kết quả các kiểm tra chất lượng và các quyết định tiền xử lý.

Mỗi dòng là trạng thái tại `observation_time`; `target_Appliances_t_plus_60m` là điện năng thiết bị tại `forecast_timestamp`, sau 6 khoảng đo 10 phút. Hai cột `rv1` và `rv2` bị loại khỏi dữ liệu mô hình vì trùng nhau hoàn toàn và là biến ngẫu nhiên, không có ý nghĩa vận hành.

Chuẩn hóa/scale không thực hiện trong notebook này. Khi huấn luyện mô hình, chỉ fit scaler trên tập train rồi mới áp dụng cho validation/test để tránh rò rỉ dữ liệu.

CSV `full` giữ 19.729 dòng, gồm 13.804 dòng train, 1.967 dòng validation, 3.946 dòng test và 12 dòng `split = gap`. Các dòng `gap` không nằm trong ba CSV riêng. Nhãn cuối cùng của train/validation luôn có timestamp nhỏ hơn thời điểm quan sát đầu tiên của tập kế tiếp.

Không đưa `split`, `observation_time`, `forecast_timestamp` hoặc cột target vào ma trận đặc trưng. Target là giá trị tại bản ghi sau 60 phút, không phải tổng điện năng trong một giờ. Hai cột thời gian dùng để truy vết và kiểm tra thứ tự.
