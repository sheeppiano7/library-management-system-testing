"""Shared helpers for the public UI test suite."""
import os
from sqlalchemy import create_engine, inspect, text

BASE = os.getenv("BOOK_BASE_URL", "http://127.0.0.1:5001")


def target_engine(kind="mysql"):
    key = {"mysql": "BOOK_MYSQL_URL", "sqlserver": "BOOK_SQLSERVER_URL", "postgresql": "BOOK_POSTGRESQL_URL"}[kind]
    url = os.getenv(key)
    if not url:
        raise RuntimeError(f"Set {key} to a dedicated test database")
    return create_engine(url, pool_pre_ping=True)


def snapshot(engine):
    names = set(inspect(engine).get_table_names())
    wanted = {"books", "readers", "borrows"}
    missing = wanted - names
    if missing:
        raise RuntimeError(f"Missing test tables: {sorted(missing)}")
    with engine.connect() as conn:
        result = {}
        for table in sorted(wanted):
            rows = conn.execute(text(f"SELECT * FROM {table}"))
            result[table] = [dict(row._mapping) for row in rows]
        return result
