\# Dữ liệu địa giới hành chính – NEU Career



\## 1. Giới thiệu



Thư mục này lưu trữ dữ liệu địa giới hành chính Việt Nam được sử dụng chung trong dự án NEU Career.



Dữ liệu hiện tại gồm:

\- 34 tỉnh/thành phố.

\- 3.321 phường/xã.



Các module sử dụng dữ liệu này:

\- \*\*Business:\*\* Chọn tỉnh/thành và phường/xã khi đăng tin tuyển dụng.

\- \*\*Student:\*\* Lọc tin tuyển dụng theo tỉnh/thành và phường/xã.

\- \*\*Admin/Moderator:\*\* Xem địa điểm làm việc khi quản lý và kiểm duyệt tin tuyển dụng.



\## 2. Cấu trúc thư mục



```text

data/

└── administrative\_units/

&#x20;   ├── README.md

&#x20;   └── Vietnamese-Administrative-Units-Dataset.csv

```



Script nhập dữ liệu nằm tại:



```text

scripts/import\_administrative\_units.py

```



Cấu trúc bảng được định nghĩa trong:



```text

db/schema.sql

```



\## 3. Cấu trúc dữ liệu trong SQLite



\### Bảng `provinces`



| Cột | Kiểu dữ liệu | Ý nghĩa |

|---|---|---|

| code | TEXT | Mã tỉnh/thành |

| name | TEXT | Tên tỉnh/thành |



\### Bảng `wards`



| Cột | Kiểu dữ liệu | Ý nghĩa |

|---|---|---|

| code | TEXT | Mã phường/xã |

| name | TEXT | Tên phường/xã |

| level | TEXT | Cấp đơn vị hành chính |

| province\_code | TEXT | Mã tỉnh/thành trực thuộc |



Các mã đơn vị hành chính được lưu dưới dạng `TEXT` để giữ nguyên số 0 ở đầu mã.



\## 4. Cách khởi tạo dữ liệu trên máy thành viên



Sau khi clone hoặc pull code mới nhất, kích hoạt môi trường ảo và đứng tại thư mục gốc dự án.



Chạy lệnh khởi tạo database:



```powershell

flask --app run.py init-db

```



Sau đó chạy script nhập dữ liệu:



```powershell

python scripts/import\_administrative\_units.py

```



Script sẽ đọc file CSV, tạo/cập nhật dữ liệu trong hai bảng `provinces` và `wards`.



Không cần tự tạo bảng hoặc nhập dữ liệu thủ công.



\## 5. Kiểm tra dữ liệu



Có thể kiểm tra bằng SQLite:



```sql

SELECT COUNT(\*) FROM provinces;

SELECT COUNT(\*) FROM wards;

```



Kết quả dự kiến:



\- `provinces`: 34 bản ghi.

\- `wards`: 3321 bản ghi.



\## 6. Ví dụ truy vấn



Lấy danh sách tỉnh/thành:



```sql

SELECT code, name

FROM provinces

ORDER BY name;

```



Lấy danh sách phường/xã thuộc một tỉnh:



```sql

SELECT code, name, level

FROM wards

WHERE province\_code = '01'

ORDER BY name;

```



Lấy danh sách phường/xã kèm tên tỉnh/thành:



```sql

SELECT

&#x20;   w.code,

&#x20;   w.name AS ward\_name,

&#x20;   w.level,

&#x20;   p.code AS province\_code,

&#x20;   p.name AS province\_name

FROM wards w

JOIN provinces p

&#x20;   ON w.province\_code = p.code

ORDER BY p.name, w.name;

```



\## 7. Quy định sử dụng chung



\- Các thành viên phải sử dụng chung hai bảng `provinces` và `wards`.

\- Không tự tạo bảng địa giới hành chính khác.

\- Không tự tải hoặc import một bộ dữ liệu khác khi chưa thống nhất.

\- Không tự ý đổi tên bảng hoặc tên cột.

\- Không sửa cấu trúc `jobs.location` nếu chưa thống nhất với nhóm.

\- Khi cần cập nhật dữ liệu, sử dụng script import chung.



\## 8. Nguồn dữ liệu



Tên bộ dữ liệu: Vietnamese Administrative Units Dataset.



Nguồn: https://github.com/mantisvn/Vietnamese-Administrative-Units-Dataset



File CSV được lưu trong thư mục này để các thành viên có thể sử dụng chung và tái tạo dữ liệu trên máy cá nhân.

