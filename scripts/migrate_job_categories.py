
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "career_connect.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

try:
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(job_categories)")
    }

    if "parent_id" not in columns:
        conn.execute("""
            ALTER TABLE job_categories
            ADD COLUMN parent_id INTEGER
            REFERENCES job_categories(id)
            ON DELETE RESTRICT
        """)

    if "level" not in columns:
        conn.execute("""
            ALTER TABLE job_categories
            ADD COLUMN level INTEGER NOT NULL DEFAULT 1
            CHECK (level IN (1, 2, 3))
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_categories_parent_id
        ON job_categories(parent_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_categories_level
        ON job_categories(level)
    """)

    conn.commit()
    print("MIGRATION THANH CONG!")

    rows = conn.execute(
        "PRAGMA table_info(job_categories)"
    ).fetchall()

    print("\nCac cot hien tai:")
    for row in rows:
        print(row[1], row[2])

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
