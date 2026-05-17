"""
신화AI부동산 — 공인중개사 설문 응답 누적 저장 (SQLite)
"""
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "responses.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """앱 기동 시 1회 호출. 테이블이 없으면 생성합니다."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS survey_responses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_at TEXT    NOT NULL,
                main_property TEXT   NOT NULL,
                ai_goals     TEXT    NOT NULL,  -- JSON 직렬화된 리스트
                ai_level     TEXT    NOT NULL
            )
            """
        )


def save_response(
    main_property: str,
    ai_goals: list[str],
    ai_level: str,
) -> int:
    """설문 응답 1건을 저장하고 새 row id를 반환합니다."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO survey_responses
                (submitted_at, main_property, ai_goals, ai_level)
            VALUES (?, ?, ?, ?)
            """,
            (now, main_property, json.dumps(ai_goals, ensure_ascii=False), ai_level),
        )
        return cur.lastrowid


def count_responses() -> int:
    """누적 응답 수를 반환합니다."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM survey_responses"
        ).fetchone()
        return int(row["c"]) if row else 0


def latest_responses(limit: int = 5) -> list[dict]:
    """최근 응답 N건을 dict 리스트로 반환합니다 (운영 모니터링용)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, submitted_at, main_property, ai_goals, ai_level
            FROM survey_responses
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "submitted_at": r["submitted_at"],
                "main_property": r["main_property"],
                "ai_goals": json.loads(r["ai_goals"]),
                "ai_level": r["ai_level"],
            }
            for r in rows
        ]
