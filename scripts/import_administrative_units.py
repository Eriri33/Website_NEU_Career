
import csv
import sys
from pathlib import Path

# Đưa thư mục gốc dự án vào Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.database import get_db


# Đường dẫn file CSV
CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "administrative_units"
    / "Vietnamese-Administrative-Units-Dataset.csv"
)


def clean_text(value):
    """Xóa khoảng trắng thừa và xuống dòng."""
    return " ".join((value or "").split())


def read_csv():
    """Đọc và chuẩn hóa dữ liệu từ CSV."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Khong tim thay file CSV: {CSV_PATH}"
        )

    provinces = {}
    wards = {}

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file, delimiter=";")

        required_columns = {
            "Mã",
            "Tên",
            "Cấp",
            "Mã TP",
            "Tỉnh / Thành Phố"
        }

        if not required_columns.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "CSV khong co day du cac cot can thiet. "
                f"Cac cot hien tai: {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader, start=2):
            ward_code = clean_text(row.get("Mã"))
            ward_name = clean_text(row.get("Tên"))
            ward_level = clean_text(row.get("Cấp"))
            province_code = clean_text(row.get("Mã TP"))
            province_name = clean_text(row.get("Tỉnh / Thành Phố"))

            # Bỏ qua dòng trống
            if not any([
                ward_code,
                ward_name,
                province_code,
                province_name
            ]):
                continue

            # Kiểm tra dữ liệu bắt buộc
            if not all([
                ward_code,
                ward_name,
                ward_level,
                province_code,
                province_name
            ]):
                raise ValueError(
                    f"Dong {row_number} bi thieu du lieu bat buoc."
                )

            # Lưu tỉnh/thành phố, tránh trùng mã
            if province_code in provinces:
                if provinces[province_code] != province_name:
                    raise ValueError(
                        f"Ma tinh {province_code} co nhieu ten khac nhau."
                    )
            else:
                provinces[province_code] = province_name

            # Lưu phường/xã, tránh trùng mã
            if ward_code in wards:
                raise ValueError(
                    f"Ma phuong/xa {ward_code} bi trung trong CSV."
                )

            wards[ward_code] = (
                ward_name,
                ward_level,
                province_code
            )

    if not provinces or not wards:
        raise ValueError("CSV khong co du lieu hop le.")

    return provinces, wards


def import_data(db, provinces, wards):
    """Tạo bảng và import dữ liệu."""

    # Bảng tỉnh/thành phố
    db.execute("""
        CREATE TABLE IF NOT EXISTS provinces (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    # Bảng phường/xã
    db.execute("""
        CREATE TABLE IF NOT EXISTS wards (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            level TEXT NOT NULL,
            province_code TEXT NOT NULL,
            FOREIGN KEY (province_code)
                REFERENCES provinces(code)
        )
    """)

    # Import tỉnh/thành phố
    for code, name in provinces.items():
        db.execute("""
            INSERT INTO provinces (code, name)
            VALUES (?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name
        """, (code, name))

    # Import phường/xã
    for code, (name, level, province_code) in wards.items():
        db.execute("""
            INSERT INTO wards (
                code,
                name,
                level,
                province_code
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                level = excluded.level,
                province_code = excluded.province_code
        """, (code, name, level, province_code))

    db.commit()


def main():
    print("=" * 65)
    print("NEU CAREER - IMPORT ADMINISTRATIVE UNITS")
    print("=" * 65)

    try:
        provinces, wards = read_csv()

        print(f"\nSo tinh/thanh doc duoc: {len(provinces)}")
        print(f"So phuong/xa doc duoc: {len(wards)}")

        app = create_app()

        with app.app_context():
            db = get_db()

            import_data(db, provinces, wards)

            province_count = db.execute(
                "SELECT COUNT(*) FROM provinces"
            ).fetchone()[0]

            ward_count = db.execute(
                "SELECT COUNT(*) FROM wards"
            ).fetchone()[0]

        print("\nIMPORT THANH CONG!")
        print(f"Tong so tinh/thanh trong DB: {province_count}")
        print(f"Tong so phuong/xa trong DB: {ward_count}")

    except Exception as error:
        print("\nIMPORT THAT BAI!")
        print(f"Loi: {error}")
        raise

    print("=" * 65)


if __name__ == "__main__":
    main()
