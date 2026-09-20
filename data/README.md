# Dữ liệu của dự án

## Nguồn và tính bất biến

- `raw/energydata_complete.csv`: bản sao nguyên trạng của UCI Appliances Energy Prediction do nhóm cung cấp.
- SHA-256 của bản raw: `2820BF712AD0275CB18B85A05250926100D8E65EBB9F4D2D016CA91EA152A25D`.
- Không sửa trực tiếp dữ liệu trong `raw/`.

## Đầu ra tiền xử lý

Các tệp dưới đây được tạo lại hoàn toàn khi chạy `notebooks/01_data_preparation.ipynb`:

- `processed/energy_forecasting_h1_full.csv`: toàn bộ các quan sát có nhãn dự báo 1 giờ.
- `processed/energy_forecasting_h1_train.csv`, `..._validation.csv`, `..._test.csv`: chia theo thời gian với tỉ lệ 70%/10%/20%.
- `processed/data_quality_summary.json`: kết quả các kiểm tra chất lượng và các quyết định tiền xử lý.

Mỗi dòng là trạng thái tại `observation_time`; `target_Appliances_t_plus_60m` là điện năng thiết bị tại `forecast_timestamp`, sau 6 khoảng đo 10 phút. Hai cột `rv1` và `rv2` bị loại khỏi dữ liệu mô hình vì trùng nhau hoàn toàn và là biến ngẫu nhiên, không có ý nghĩa vận hành.

Chuẩn hóa/scale không thực hiện trong notebook này. Khi huấn luyện mô hình, chỉ fit scaler trên tập train rồi mới áp dụng cho validation/test để tránh rò rỉ dữ liệu.
