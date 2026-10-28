import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
from pathlib import Path

def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    schema_path = Path(current_app.root_path).parent / "db" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create database tables from db/schema.sql."""
    init_db()
    click.echo("Initialized the Career Connect database.")

def init_app(app):
    app.teardown_appcontext(close_db)
