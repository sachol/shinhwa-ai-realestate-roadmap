"""
신화AI부동산 — 공인중개사 설문 응답 누적 저장 (SQLite)
"""
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "responses.db"

_REQUIRED_COLUMNS: dict[str, str] = {
    "submitted_at":   "TEXT NOT NULL DEFAULT ''",
    "business_name":  "TEXT NOT NULL DEFAULT ''",
    "user_name":      "TEXT NOT NULL DEFAULT ''",
    "main_property":  "TEXT NOT NULL DEFAULT ''",
    "custom_property":"TEXT NOT NULL DEFAULT ''",
    "ai_goals":       "TEXT NOT NULL DEFAULT ''",
    "custom_goals":   "TEXT NOT NULL DEFAULT ''",
    "ai_level":       "TEXT NOT NULL DEFAULT ''",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS survey_responses (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(survey_responses)")}
        for col, ddl in _REQUIRED_COLUMNS.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE survey_responses ADD COLUMN {col} {ddl}")


def save_response(
    *,
    business_name: str,
    user_name: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO survey_responses
                (submitted_at, business_name, user_name,
                 main_property, custom_property,
                 ai_goals, custom_goals, ai_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                business_name,
                user_name,
                json.dumps(main_property, ensure_ascii=False),
                custom_property,
                json.dumps(ai_goals, ensure_ascii=False),
                custom_goals,
                ai_level,
            ),
        )
        return cur.lastrowid


def count_responses() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM survey_responses").fetchone()
        return int(row["c"]) if row else 0


def latest_responses(limit: int = 5) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, submitted_at, business_name, user_name,
                   main_property, custom_property,
                   ai_goals, custom_goals, ai_level
            FROM survey_responses
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        result = []
        for r in rows:
            try:
                mp = json.loads(r["main_property"]) if r["main_property"] else []
            except (json.JSONDecodeError, TypeError):
                mp = [r["main_property"]] if r["main_property"] else []
            try:
                ag = json.loads(r["ai_goals"]) if r["ai_goals"] else []
            except (json.JSONDecodeError, TypeError):
                ag = [r["ai_goals"]] if r["ai_goals"] else []
            result.append({
                "id": r["id"],
                "submitted_at": r["submitted_at"],
                "business_name": r["business_name"] or "",
                "user_name": r["user_name"] or "",
                "main_property": mp,
                "custom_property": r["custom_property"] or "",
                "ai_goals": ag,
                "custom_goals": r["custom_goals"] or "",
                "ai_level": r["ai_level"] or "",
            })
        return result
