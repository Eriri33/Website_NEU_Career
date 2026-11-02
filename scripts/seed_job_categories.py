
import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "db"
    / "career_connect.db"
)


# Cấu trúc:
# Cấp 1: Nhóm nghề
# Cấp 2: Nghề
# Cấp 3: Vị trí chuyên môn

CATEGORIES = {
    "Công nghệ thông tin": {
        "Software Engineering": [
            "Software Engineer",
            "Backend Developer",
            "Frontend Developer",
            "Mobile Developer",
            "Fullstack Developer",
            "Blockchain Engineer"
        ],

        "Software Testing": [
            "Software Tester (Automation & Manual)",
            "Automation Tester",
            "Manual Tester",
            "Game Tester",
            "QA Engineer",
            "Process Quality Assurance (PQA)"
        ],

        "Artificial Intelligence (AI)": [
            "AI Engineer",
            "AI Researcher",
            "Data Labeling"
        ],

        "Data Science": [
            "Data Analyst",
            "Data Scientist",
            "Data Engineer",
            "Business Intelligence Analyst"
        ],

        "Cybersecurity": [
            "Cybersecurity Engineer",
            "Security Analyst",
            "Penetration Tester",
            "Information Security Specialist"
        ],

        "IT Support & Infrastructure": [
            "IT Support Specialist",
            "System Administrator",
            "Network Engineer",
            "Cloud Engineer",
            "DevOps Engineer"
        ]
    },

    "Marketing và truyền thông": {
        "Marketing tổng hợp": [
            "Nhân viên Marketing",
            "Chuyên viên Marketing",
            "Trưởng phòng Marketing",
            "Giám đốc Marketing"
        ],

        "Marketing kỹ thuật số": [
            "Chuyên viên Digital Marketing",
            "Chuyên viên SEO",
            "Chuyên viên quảng cáo trực tuyến",
            "Chuyên viên Email Marketing"
        ],

        "Nội dung và sáng tạo": [
            "Chuyên viên Content Marketing",
            "Biên tập viên nội dung",
            "Người sáng tạo nội dung",
            "Quản lý nội dung"
        ],

        "Truyền thông và quan hệ công chúng": [
            "Chuyên viên truyền thông",
            "Chuyên viên quan hệ công chúng",
            "Chuyên viên tổ chức sự kiện",
            "Chuyên viên truyền thông nội bộ"
        ]
    },

    "Kinh doanh và bán hàng": {
        "Phát triển kinh doanh": [
            "Nhân viên phát triển kinh doanh",
            "Chuyên viên phát triển thị trường",
            "Trưởng nhóm phát triển kinh doanh",
            "Giám đốc phát triển kinh doanh"
        ],

        "Bán hàng": [
            "Nhân viên kinh doanh",
            "Nhân viên tư vấn bán hàng",
            "Trưởng nhóm kinh doanh",
            "Trưởng phòng kinh doanh"
        ],

        "Quản lý khách hàng": [
            "Chuyên viên quản lý khách hàng",
            "Chuyên viên chăm sóc khách hàng doanh nghiệp",
            "Quản lý khách hàng trọng điểm"
        ],

        "Thương mại điện tử": [
            "Nhân viên vận hành sàn thương mại điện tử",
            "Chuyên viên thương mại điện tử",
            "Quản lý gian hàng trực tuyến"
        ]
    },

    "Tài chính và kế toán": {
        "Kế toán": [
            "Kế toán tổng hợp",
            "Kế toán nội bộ",
            "Kế toán thuế",
            "Kế toán thanh toán",
            "Kế toán trưởng"
        ],

        "Kiểm toán": [
            "Trợ lý kiểm toán",
            "Kiểm toán viên",
            "Kiểm toán nội bộ",
            "Trưởng nhóm kiểm toán"
        ],

        "Tài chính doanh nghiệp": [
            "Chuyên viên phân tích tài chính",
            "Chuyên viên hoạch định tài chính",
            "Chuyên viên quản lý ngân sách",
            "Giám đốc tài chính"
        ],

        "Ngân hàng": [
            "Nhân viên tín dụng",
            "Chuyên viên quan hệ khách hàng",
            "Giao dịch viên ngân hàng",
            "Chuyên viên thanh toán quốc tế"
        ],

        "Chứng khoán và đầu tư": [
            "Chuyên viên tư vấn đầu tư",
            "Chuyên viên phân tích đầu tư",
            "Chuyên viên môi giới chứng khoán",
            "Chuyên viên quản lý danh mục đầu tư"
        ]
    },

    "Nhân sự, hành chính và pháp chế": {
        "Tuyển dụng": [
            "Chuyên viên tuyển dụng",
            "Nhân viên tuyển dụng",
            "Trưởng nhóm tuyển dụng",
            "Trưởng phòng tuyển dụng"
        ],

        "Quản trị nhân sự": [
            "Chuyên viên nhân sự",
            "Chuyên viên đào tạo và phát triển",
            "Chuyên viên tiền lương và phúc lợi",
            "Trưởng phòng nhân sự"
        ],

        "Hành chính văn phòng": [
            "Nhân viên hành chính",
            "Nhân viên lễ tân",
            "Trợ lý giám đốc",
            "Thư ký văn phòng"
        ],

        "Pháp chế": [
            "Chuyên viên pháp chế",
            "Trợ lý pháp lý",
            "Chuyên viên tuân thủ",
            "Trưởng phòng pháp chế"
        ]
    },

    "Chăm sóc khách hàng và vận hành": {
        "Chăm sóc khách hàng": [
            "Nhân viên chăm sóc khách hàng",
            "Nhân viên tổng đài",
            "Chuyên viên hỗ trợ khách hàng",
            "Trưởng nhóm chăm sóc khách hàng"
        ],

        "Quản lý vận hành": [
            "Nhân viên vận hành",
            "Chuyên viên quản lý vận hành",
            "Giám sát vận hành",
            "Trưởng phòng vận hành"
        ],

        "Du lịch và khách sạn": [
            "Nhân viên điều hành tour",
            "Nhân viên lễ tân khách sạn",
            "Nhân viên đặt phòng",
            "Quản lý khách sạn"
        ],

        "Nhà hàng và dịch vụ ăn uống": [
            "Nhân viên phục vụ",
            "Nhân viên pha chế",
            "Giám sát nhà hàng",
            "Quản lý nhà hàng"
        ]
    },

    "Thiết kế và sáng tạo": {
        "Thiết kế đồ họa": [
            "Nhân viên thiết kế đồ họa",
            "Chuyên viên thiết kế thương hiệu",
            "Chuyên viên thiết kế quảng cáo",
            "Trưởng nhóm thiết kế"
        ],

        "Thiết kế giao diện": [
            "Chuyên viên thiết kế UI",
            "Chuyên viên thiết kế UX",
            "Chuyên viên thiết kế UI/UX",
            "Trưởng nhóm thiết kế sản phẩm"
        ],

        "Sản xuất hình ảnh và video": [
            "Nhiếp ảnh gia",
            "Nhân viên quay dựng video",
            "Biên tập video",
            "Đạo diễn hình ảnh"
        ]
    },

    "Logistics và chuỗi cung ứng": {
        "Xuất nhập khẩu": [
            "Nhân viên xuất nhập khẩu",
            "Nhân viên chứng từ xuất nhập khẩu",
            "Chuyên viên khai báo hải quan",
            "Trưởng nhóm xuất nhập khẩu"
        ],

        "Kho vận và vận tải": [
            "Nhân viên kho",
            "Thủ kho",
            "Điều phối vận tải",
            "Quản lý kho"
        ],

        "Quản lý chuỗi cung ứng": [
            "Chuyên viên chuỗi cung ứng",
            "Chuyên viên hoạch định nhu cầu",
            "Chuyên viên thu mua",
            "Trưởng phòng chuỗi cung ứng"
        ]
    },

    "Kỹ thuật và sản xuất": {
        "Kỹ thuật cơ khí": [
            "Kỹ sư cơ khí",
            "Kỹ thuật viên cơ khí",
            "Kỹ sư thiết kế cơ khí"
        ],

        "Kỹ thuật điện và điện tử": [
            "Kỹ sư điện",
            "Kỹ sư điện tử",
            "Kỹ thuật viên điện",
            "Kỹ sư tự động hóa"
        ],

        "Quản lý sản xuất": [
            "Nhân viên kế hoạch sản xuất",
            "Giám sát sản xuất",
            "Quản lý sản xuất",
            "Trưởng phòng sản xuất"
        ],

        "Quản lý chất lượng": [
            "Nhân viên kiểm soát chất lượng",
            "Kỹ sư đảm bảo chất lượng",
            "Chuyên viên quản lý chất lượng",
            "Trưởng phòng chất lượng"
        ]
    },

    "Giáo dục và đào tạo": {
        "Giảng dạy": [
            "Giáo viên mầm non",
            "Giáo viên tiểu học",
            "Giáo viên trung học",
            "Giảng viên đại học"
        ],

        "Đào tạo và phát triển": [
            "Chuyên viên đào tạo",
            "Chuyên viên phát triển chương trình đào tạo",
            "Trợ giảng",
            "Quản lý đào tạo"
        ],

        "Tư vấn giáo dục": [
            "Chuyên viên tư vấn tuyển sinh",
            "Chuyên viên tư vấn du học",
            "Chuyên viên hướng nghiệp"
        ]
    }
}

def make_unique_name(name, context, used_names):
    result = name

    if result in used_names:
        result = f"{name} ({context})"

    index = 2
    original = result

    while result in used_names:
        result = f"{original} {index}"
        index += 1

    used_names.add(result)
    return result
def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # Không seed nếu bảng đã có dữ liệu
        count = conn.execute(
            "SELECT COUNT(*) FROM job_categories"
        ).fetchone()[0]

        if count > 0:
            raise Exception(
                f"Bảng job_categories hiện có {count} bản ghi. "
                "Dừng seed để tránh thêm trùng dữ liệu."
            )

        total = 0
        used_names = set()
        for level1_name, level2_categories in CATEGORIES.items():
            level1_name = make_unique_name(
            level1_name, "Nhóm nghề", used_names
            )
            # Tạo danh mục cấp 1
            cur = conn.execute("""
                INSERT INTO job_categories (
                    parent_id, level, name, description, is_active
                )
                VALUES (NULL, 1, ?, '', 1)
            """, (level1_name,))

            level1_id = cur.lastrowid
            total += 1

            for level2_name, level3_categories in level2_categories.items():
                level2_name = make_unique_name(
                level2_name, level1_name, used_names
                )
                # Tạo danh mục cấp 2
                cur = conn.execute("""
                    INSERT INTO job_categories (
                        parent_id, level, name, description, is_active
                    )
                    VALUES (?, 2, ?, '', 1)
                """, (level1_id, level2_name))

                level2_id = cur.lastrowid
                total += 1

                for level3_name in level3_categories:
                    level3_name = make_unique_name(
                    level3_name, level2_name, used_names
                    )

                    # Tạo danh mục cấp 3
                    conn.execute("""
                        INSERT INTO job_categories (
                            parent_id, level, name, description, is_active
                        )
                        VALUES (?, 3, ?, '', 1)
                    """, (level2_id, level3_name))

                    total += 1

        conn.commit()

        print("DA THEM DANH MUC NGHE NGHIEP THANH CONG!")
        print("Tong so danh muc:", total)

        for level in (1, 2, 3):
            count = conn.execute("""
                SELECT COUNT(*)
                FROM job_categories
                WHERE level = ?
            """, (level,)).fetchone()[0]

            print(f"Cap {level}: {count} danh muc")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
