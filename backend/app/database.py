import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
from pathlib import Path
from app.textutil import fold_text

def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Hàm SQL fold(): so khớp tìm kiếm không phân biệt hoa/thường và dấu tiếng Việt.
        g.db.create_function("fold", 1, fold_text, deterministic=True)
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Cột bổ sung theo API_CONTRACT mục 14. Danh sách (bảng, cột, định nghĩa) để migration idempotent.
MIGRATION_COLUMNS = [
    ("jobs", "saturday_policy",
     "TEXT NOT NULL DEFAULT 'unknown' CHECK (saturday_policy IN ('off','working','negotiable','unknown'))"),
    ("jobs", "salary_text", "TEXT NOT NULL DEFAULT 'Thỏa thuận'"),
    ("companies", "company_size", "TEXT NOT NULL DEFAULT ''"),
    ("companies", "business_industries", "TEXT NOT NULL DEFAULT ''"),
    ("companies", "primary_industry", "TEXT NOT NULL DEFAULT ''"),
    ("companies", "address", "TEXT NOT NULL DEFAULT ''"),
]


def migrate_db(db):
    """Thêm cột còn thiếu vào database cũ mà không xóa dữ liệu. An toàn khi chạy nhiều lần."""
    project_root = Path(__file__).resolve().parents[2]
    module_schema_path = project_root / "db" / "module_tables.sql"
    with open(module_schema_path, "r", encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())
    for table, column, definition in MIGRATION_COLUMNS:
        existing = {row[1] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
        if existing and column not in existing:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    db.commit()


def init_db():
    db = get_db()
    project_root = Path(current_app.config["PROJECT_ROOT"])
    schema_path = project_root / "db" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    module_schema_path = project_root / "db" / "module_tables.sql"
    with open(module_schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()
    migrate_db(db)

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create database tables from db/schema.sql and db/module_tables.sql."""
    init_db()
    click.echo("Initialized the Career Connect database.")

def init_app(app):
    app.teardown_appcontext(close_db)
