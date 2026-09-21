"""Public, environment-driven configuration with no real credentials."""
import os
from pathlib import Path
from urllib.parse import urlparse


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    database = urlparse(value).path.rsplit("/", 1)[-1].split("?", 1)[0].lower()
    if database == "book_manage":
        raise RuntimeError("Refusing to connect to the original book_manage database")
    return value


DB_CONFIG = {
    "mysql": _required("BOOK_MYSQL_URL"),
    "sqlserver": _required("BOOK_SQLSERVER_URL"),
    "postgresql": _required("BOOK_POSTGRESQL_URL"),
}
EMAIL_CONFIG = {"smtp_server": "", "smtp_port": 465, "sender_email": "", "sender_password": "", "admin_email": ""}
SYNC_CONFIG = {"real_time_sync": False, "periodic_sync": False, "sync_hour": 2, "sync_minute": 0}
BORROW_CONFIG = {"max_borrow_days": 30, "overdue_reminder_days": 7}
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = str(BASE_DIR / "logs")
REPORT_DIR = str(BASE_DIR / "reports")
