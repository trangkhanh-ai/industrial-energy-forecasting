# Industrial Energy Forecasting

Tiền xử lý dữ liệu UCI Appliances Energy Prediction để dự báo điện năng thiết bị
sau 60 phút (6 bước đo, mỗi bước 10 phút). Repository hiện gồm notebook chuẩn bị
dữ liệu và báo cáo EDA; chưa có mô hình huấn luyện hay kết quả đánh giá dự báo.
Dữ liệu đo trong nhà ở, được dùng làm bài toán thực hành theo định hướng Industrial AI.

## Cài đặt và chạy

Dùng Python 3.12, chạy các lệnh sau từ thư mục gốc repository:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts/run_preprocessing.py
.venv\Scripts\python -m unittest discover -s tests -v
```

Trên Linux/macOS, thay `.venv\Scripts\python` bằng `.venv/bin/python`.
Lệnh tiền xử lý chạy toàn bộ notebook bằng kernel mới, lưu output notebook và tạo
lại CSV cùng biểu đồ. Có thể mở notebook bằng Jupyter hoặc VS Code và chọn môi trường
đã cài các thư viện trên để chạy từng cell.

## Cấu trúc

- `notebooks/01_data_preparation.ipynb`: kiểm tra dữ liệu, EDA, tạo nhãn và chia tập.
- `data/raw/energydata_complete.csv`: dữ liệu gốc; không ghi đè.
- `data/processed/`: dữ liệu đầu ra và báo cáo chất lượng.
- `reports/figures/01_daily_weekly_cycles.png`: biểu đồ chu kỳ ngày/tuần.
- `reports/lights-zero-vs-positive.html`: so sánh hai trạng thái đèn; mở bằng trình duyệt, cần mạng để tải D3.
- `tests/`: kiểm tra thực thi notebook, tính đúng của nhãn, ranh giới tập và dữ liệu lỗi.

## Quy ước dữ liệu

`Appliances_lag_0` là điện năng đã biết tại `observation_time`, còn
`target_Appliances_t_plus_60m` là điện năng của bản ghi sau 60 phút, không phải tổng
điện năng tiêu thụ trong một giờ. Đặc trưng lịch lấy từ `forecast_timestamp`.

Chia theo thời gian với ranh giới danh nghĩa 70%/10%/20%. Loại 6 dòng cuối train
và 6 dòng cuối validation để nhãn không lấn sang thời gian quan sát của tập sau.
Các dòng bị loại vẫn nằm trong CSV `full` với `split = gap`.

Khi huấn luyện, đọc ba CSV riêng; loại `split`, hai cột timestamp và cột target
khỏi đầu vào mô hình. Chỉ fit scaler trên train. Báo cáo EDA mô tả toàn bộ dữ liệu;
không dùng thống kê test để chọn đặc trưng hoặc điều chỉnh mô hình.

Xem [mô tả dữ liệu](data/README.md) để biết checksum và đầu ra chi tiết.
