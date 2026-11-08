# Tìm kiếm không dấu
import unicodedata


def fold_text(value):
    """'Hà Nội' -> 'ha noi'; 'ĐẠI HỌC' -> 'dai hoc'. None -> ''."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFD", str(value))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "d").lower().strip()


def like_pattern(value):
    """Tạo mẫu LIKE '%...%' đã fold và escape % _ \\ (dùng kèm `ESCAPE '\\'`)."""
    text = fold_text(value)
    text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{text}%"
