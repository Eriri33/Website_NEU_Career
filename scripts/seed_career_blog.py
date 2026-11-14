"""Nạp các bài viết hướng nghiệp mẫu để khởi tạo trang blog.

    python scripts/seed_career_blog.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.database import get_db, init_db

ARTICLES = [
    (
        "Viết CV thực tập: tập trung vào tiềm năng và trải nghiệm",
        "Cách trình bày CV rõ ràng khi bạn chưa có nhiều kinh nghiệm làm việc.",
        "CV",
        """Một CV thực tập tốt không cần thật dài. Nhà tuyển dụng cần nhanh chóng hiểu bạn đang học gì, có thể đóng góp điều gì và mong muốn học hỏi ra sao. Hãy ưu tiên thông tin liên quan đến vị trí ứng tuyển thay vì liệt kê mọi hoạt động bạn từng tham gia.

Bắt đầu bằng thông tin liên hệ chuyên nghiệp và một phần giới thiệu ngắn từ hai đến ba câu. Nêu ngành học, định hướng gần nhất và một hoặc hai thế mạnh có liên quan. Tránh những mô tả chung chung như “chăm chỉ, chịu khó” nếu không có ví dụ cụ thể.

Khi chưa có kinh nghiệm chính thức, hãy dùng dự án môn học, hoạt động câu lạc bộ, cuộc thi hoặc công việc bán thời gian. Với mỗi trải nghiệm, mô tả nhiệm vụ của bạn, cách bạn thực hiện và kết quả có thể kiểm chứng. Chẳng hạn, thay vì viết “tham gia truyền thông”, hãy nêu bạn đã lên lịch nội dung, phối hợp với nhóm và theo dõi chỉ số nào.

Điều chỉnh CV cho từng vị trí bằng cách đối chiếu yêu cầu tuyển dụng với kỹ năng và dự án thực tế của bạn. Dùng từ ngữ cụ thể, kiểm tra lỗi chính tả và giữ định dạng nhất quán. Nếu gửi tệp đính kèm, đặt tên dễ nhận biết như HoTen_CV_ThucTap.pdf.

Trước khi gửi, hãy đọc CV như một nhà tuyển dụng: thông tin quan trọng có dễ tìm không, mỗi gạch đầu dòng có nói rõ đóng góp của bạn không, và mọi chi tiết đều trung thực không? Một bản CV gọn gàng, đúng trọng tâm thường tạo ấn tượng tốt hơn một bản nhiều thông tin nhưng khó đọc."""
    ),
    (
        "Chọn kỳ thực tập đầu tiên: 5 điều nên cân nhắc",
        "Đánh giá cơ hội thực tập dựa trên nội dung công việc, người hướng dẫn và mục tiêu học tập.",
        "Thực tập",
        """Kỳ thực tập đầu tiên là cơ hội để thử áp dụng kiến thức vào môi trường thật. Đừng chỉ chọn vị trí dựa trên tên công ty hoặc chức danh; hãy tìm hiểu công việc hằng ngày và những điều bạn có thể học được.

Thứ nhất, xem nhiệm vụ có liên quan đến lĩnh vực bạn muốn khám phá không. Một mô tả rõ ràng về đầu việc, công cụ và nhóm phối hợp giúp bạn hình dung trải nghiệm thực tế. Nếu thông tin còn mơ hồ, hãy hỏi thêm trong buổi trao đổi.

Thứ hai, tìm hiểu cách doanh nghiệp hướng dẫn thực tập sinh. Người phụ trách, quy trình phản hồi và mục tiêu theo từng giai đoạn sẽ giúp bạn học nhanh hơn. Bạn có thể hỏi ai sẽ giao việc, tần suất trao đổi ra sao và kết quả nào được kỳ vọng.

Thứ ba, cân đối lịch học, thời gian di chuyển và lịch làm việc. Hãy xác nhận số buổi, thời gian bắt đầu, hình thức làm việc và khả năng linh hoạt trong mùa thi. Điều kiện phù hợp giúp bạn duy trì việc học và hoàn thành cam kết với doanh nghiệp.

Cuối cùng, tìm hiểu quyền lợi, hỗ trợ và các điều khoản liên quan trước khi nhận lời. Đặt câu hỏi lịch sự về phụ cấp, giấy tờ, bảo mật hoặc đánh giá thực tập. Một lựa chọn tốt không nhất thiết phải hoàn hảo ở mọi mặt; quan trọng là nó giúp bạn tiến gần hơn đến mục tiêu và có môi trường để phát triển."""
    ),
    (
        "Phỏng vấn theo STAR: kể câu chuyện kinh nghiệm rõ ràng",
        "Dùng bốn bước Situation, Task, Action, Result để trả lời câu hỏi hành vi mạch lạc hơn.",
        "Phỏng vấn",
        """Những câu hỏi như “Hãy kể về lần bạn giải quyết một vấn đề khó” thường khiến ứng viên trả lời lan man. Cách STAR giúp bạn sắp xếp câu chuyện theo bốn phần: Situation (bối cảnh), Task (nhiệm vụ), Action (hành động) và Result (kết quả).

Ở phần bối cảnh, nói ngắn gọn điều gì đang diễn ra và ai có liên quan. Phần nhiệm vụ làm rõ mục tiêu hoặc trách nhiệm của bạn. Sau đó, dành nhiều thời gian nhất cho hành động: bạn đã phân tích, trao đổi, thử nghiệm hay phối hợp như thế nào? Cuối cùng, kết quả cho biết việc làm đó tạo ra thay đổi gì và bạn học được gì.

Bạn không nhất thiết phải có kinh nghiệm đi làm để sử dụng STAR. Một dự án trên lớp, hoạt động câu lạc bộ hoặc công việc tình nguyện đều có thể trở thành ví dụ nếu bạn nêu rõ vai trò của mình. Hãy phân biệt đóng góp cá nhân với kết quả chung của cả nhóm.

Trước buổi phỏng vấn, chuẩn bị vài câu chuyện về làm việc nhóm, xử lý khó khăn, học kỹ năng mới và nhận phản hồi. Ghi lại các ý chính thay vì học thuộc từng câu để câu trả lời tự nhiên hơn. Nếu có số liệu, chỉ sử dụng những con số bạn có thể giải thích và xác minh.

Sau khi kể xong, dừng lại để nhà tuyển dụng có thể hỏi sâu hơn. Câu trả lời tốt không phải là câu chuyện hoàn hảo, mà là câu chuyện chân thực cho thấy cách bạn suy nghĩ, hành động và rút kinh nghiệm."""
    ),
]


def main():
    app = create_app()
    with app.app_context():
        db = get_db()
        if not db.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'career_contents'").fetchone():
            init_db()
        inserted = 0
        for title, summary, category, body in ARTICLES:
            exists = db.execute(
                "SELECT 1 FROM career_contents WHERE title = ?",
                (title,)
            ).fetchone()
            if exists:
                continue
            db.execute(
                """INSERT INTO career_contents (title, summary, category, body, status)
                   VALUES (?, ?, ?, ?, 'published')""",
                (title, summary, category, body)
            )
            inserted += 1
        db.commit()
        print(f"Added {inserted} career articles.")


if __name__ == "__main__":
    main()
