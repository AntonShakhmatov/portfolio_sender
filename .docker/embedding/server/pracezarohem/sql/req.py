# db.py
from __future__ import annotations
import os
import re
import time
import json
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional
from typing import List
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.engine import Engine

DB_DSN = "mysql+pymysql://test:test@database/test?charset=utf8mb4"

engine: Engine = create_engine(DB_DSN, future=True)
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

def _fetch_default_professions(engine: Engine, table: str, column: str, attempts: int = 5, delay: float = 0.3) -> List[str]:
    sql = text(f'SELECT `{column}` FROM `{table}` ORDER BY id DESC LIMIT 1')  # для MySQL кавычки — обратные апострофы
    for _ in range(10):
        with engine.begin() as conn:
            row = conn.execute(sql).fetchone()
        if not row or row[0] in (None, ''):
            time.sleep(0.3)
            continue

        val = row[0]

        # Если колонка JSON — драйвер MySQL может вернуть уже list
        if isinstance(val, list):
            return [str(x).strip() for x in val if str(x).strip()]

        # Если пришла строка с JSON — распарсим
        if isinstance(val, str):
            try:
                arr = json.loads(val)
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr if str(x).strip()]
            except json.JSONDecodeError:
                # на всякий случай: CSV «a,b,c»
                return [p.strip() for p in val.split(',') if p.strip()]

        # fallback
        return [str(val).strip()] if str(val).strip() else []

    return []

def _fetch_default_phone(table: str, column: str) -> str:
    sql = text(f"SELECT {column} FROM {table} ORDER BY id DESC LIMIT 1")
    for attempt in range(20):
        try:
            with _get_engine().connect() as conn:
                row = conn.execute(sql).first()
                raw: str = (row[0] or "") if row else ""
                phone = raw.strip()

                # убрать пробелы/дефисы/скобки
                phone = re.sub(r"[ \-\(\)]", "", phone)

                # убрать префикс страны: +420 или 00420
                phone = re.sub(r"^(?:\+?420|00420)", "", phone)

                return phone
        except (OperationalError, SQLAlchemyError) as e:
            print(f"[warn] DB error (attempt {attempt+1}/20): {e}")
            time.sleep(1.5)
    return ""

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


def _canon_url(raw: str) -> str:
    """
    Канонизация ссылки на вакансию:
    - приводим схему/хост к нижнему регистру
    - выкидываем UTM/трекинг (utm_*, gclid и т.п.)
    - сортируем параметры запроса
    """
    u = urlparse(raw.strip())
    scheme = (u.scheme or 'https').lower()
    netloc = (u.netloc or '').lower()
    path = u.path or '/'
    # оставим только «полезные» query-параметры
    allowed = []
    for k, v in parse_qsl(u.query, keep_blank_values=True):
        kk = k.lower()
        if kk.startswith('utm_') or kk in ('gclid','fbclid','yclid'):
            continue
        allowed.append((k, v))
    query = urlencode(sorted(allowed))
    return urlunparse((scheme, netloc, path, '', query, ''))

def _url_hash(url_canon: str) -> bytes:
    return hashlib.sha256(url_canon.encode('utf-8')).digest()

def has_job_been_applied(url: str) -> bool:
    url_canon = _canon_url(url)
    h = _url_hash(url_canon)
    sql = text("SELECT 1 FROM applied_jobs WHERE url_hash = :h LIMIT 1")
    with _get_engine().begin() as conn:
        return conn.execute(sql, {"h": h}).fetchone() is not None

def mark_job_applied(url: str, city: str, profession: str, status: str = 'sent', note: str | None = None) -> None:
    url_canon = _canon_url(url)              # канонизированная ссылка (строка)
    h = _url_hash(url_canon)                 # bytes длиной 32 (sha256), под BINARY(32)

    sql = text("""
        INSERT INTO applied_jobs (url_hash, city, profession, status, note)
        VALUES (:h, :city, :profession, :status, :note)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            note   = VALUES(note)
    """)

    with _get_engine().begin() as conn:
        conn.execute(sql, {
            "h": h,                          # <-- hash (bytes) идёт в :h
            "city": city,
            "profession": profession,
            "status": status,
            "note": note,
        })


# def get_default_profession() -> str: return _fetch_default_field("profile_skills", "skills")
def get_default_profession() -> List[str]: return _fetch_default_professions(engine, table = "profile_skills", column = "skills")
def get_default_name() -> str:       return _fetch_default_field("profiles", "name")
def get_default_lastname() -> str:   return _fetch_default_field("profiles", "lastname")
def get_default_phone() -> str:      return _fetch_default_phone("profiles", "phone")
def get_default_email() -> str:      return _fetch_default_field("profiles", "email")
def get_default_summary() -> str:    return _fetch_default_field("profile_skills", "summary")
def get_default_skills() -> str:     return _fetch_default_field("profile_skills", "skills")
def get_default_location() -> str:   return _fetch_default_field("profiles", "location")
