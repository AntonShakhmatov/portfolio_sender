# db.py
import os
import time
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError


def _db_url() -> str:
    # если задан корректный DATABASE_URL — используем его
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # собираем из DB_* (твои переменные из docker-compose)
    host = os.getenv("DB_HOST", "database")
    port = os.getenv("DB_PORT", "3306")  # ВАЖНО: 3306 для MariaDB/MySQL
    user = os.getenv("DB_USER", "test")
    pwd  = os.getenv("DB_PASS", "test")
    name = os.getenv("DB_NAME", "test")
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}"


def _get_engine():
    return create_engine(_db_url(), pool_pre_ping=True, future=True)


def _fetch_default_field(table: str, column: str) -> str:
    sql = text(f"SELECT {column} FROM {table} ORDER BY id DESC LIMIT 1")
    for attempt in range(20):  # мягкие ретраи на случай, если DB ещё встаёт
        try:
            with _get_engine().connect() as conn:
                row = conn.execute(sql).first()
                val: Optional[str] = row[0] if row else ""
                return (val or "").strip()
        except (OperationalError, SQLAlchemyError) as e:
            print(f"[warn] DB error (attempt {attempt+1}/20): {e}")
            time.sleep(1.5)
    # return ""
    return None


def get_default_profession() -> str: return _fetch_default_field("profile_skills", "skills")
def get_default_name() -> str:       return _fetch_default_field("profiles", "name")
def get_default_lastname() -> str:   return _fetch_default_field("profiles", "lastname")
def get_default_phone() -> str:      return _fetch_default_field("profiles", "phone")
def get_default_email() -> str:      return _fetch_default_field("profiles", "email")
def get_default_summary() -> str:    return _fetch_default_field("profile_skills", "summary")
def get_default_skills() -> str:     return _fetch_default_field("profile_skills", "skills")
def get_default_location() -> str:   return _fetch_default_field("profiles", "location")
