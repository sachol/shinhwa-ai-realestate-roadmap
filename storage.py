"""
신화AI부동산 — 응답 저장소 (Google Sheets 우선, 미설정 시 SQLite로 폴백)

Secrets 구성 예시 (.streamlit/secrets.toml):
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "xxx@yyy.iam.gserviceaccount.com"
...

[sheets]
spreadsheet_id = "구글시트 URL의 /d/ 와 /edit 사이 ID"
worksheet_name = "responses"

[admin]
password = "원하는 관리자 비밀번호"
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any

import streamlit as st

from db import (
    init_db as _sqlite_init,
    save_response as _sqlite_save,
    count_responses as _sqlite_count,
    latest_responses as _sqlite_latest,
)

# ─────────────────────────────────────────────
# Google Sheets 백엔드 (gspread)
# ─────────────────────────────────────────────
COLUMNS = [
    "id",
    "submitted_at",
    "business_name",
    "user_name",
    "email",
    "main_property",
    "custom_property",
    "ai_goals",
    "custom_goals",
    "ai_level",
]


@st.cache_resource(show_spinner=False)
def _get_worksheet():
    """Streamlit secrets에 서비스 계정이 설정돼 있으면 워크시트 핸들을 반환, 없으면 None."""
    try:
        if "gcp_service_account" not in st.secrets:
            return None
        if "sheets" not in st.secrets:
            return None
    except Exception:
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds_info = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = st.secrets["sheets"]["spreadsheet_id"]
        ws_name = st.secrets["sheets"].get("worksheet_name", "responses")
        sh = client.open_by_key(sheet_id)
        try:
            ws = sh.worksheet(ws_name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=ws_name, rows=2000, cols=len(COLUMNS))
        # 헤더 보장
        existing = ws.row_values(1)
        if existing != COLUMNS:
            ws.update("A1", [COLUMNS])
        return ws
    except Exception as e:
        st.warning(f"⚠️ Google Sheets 연결 실패, 로컬 SQLite로 폴백합니다: {e}")
        return None


def _next_id(ws) -> int:
    col_a = ws.col_values(1)  # 헤더 + id들
    nums = [int(v) for v in col_a[1:] if str(v).isdigit()]
    return (max(nums) + 1) if nums else 1


# ─────────────────────────────────────────────
# 공개 API (storage 인터페이스)
# ─────────────────────────────────────────────
def init_storage() -> None:
    """앱 기동 시 호출. SQLite는 항상 초기화하고, 시트는 lazy-init."""
    _sqlite_init()


def is_sheets_active() -> bool:
    return _get_worksheet() is not None


def save_response(
    *,
    business_name: str,
    user_name: str,
    email: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> int:
    ws = _get_worksheet()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ws is not None:
        new_id = _next_id(ws)
        ws.append_row(
            [
                new_id,
                now,
                business_name,
                user_name,
                email,
                ", ".join(main_property),
                custom_property,
                ", ".join(ai_goals),
                custom_goals,
                ai_level,
            ],
            value_input_option="USER_ENTERED",
        )
        return new_id
    # 폴백: SQLite (이메일은 별도 컬럼이 db.py에 추가됨)
    return _sqlite_save(
        business_name=business_name,
        user_name=user_name,
        email=email,
        main_property=main_property,
        custom_property=custom_property,
        ai_goals=ai_goals,
        custom_goals=custom_goals,
        ai_level=ai_level,
    )


def count_responses() -> int:
    ws = _get_worksheet()
    if ws is not None:
        try:
            col = ws.col_values(1)
            return max(0, len(col) - 1)  # 헤더 제외
        except Exception:
            return _sqlite_count()
    return _sqlite_count()


def all_responses() -> list[dict[str, Any]]:
    """관리자 모드 전용 — 전체 응답 반환."""
    ws = _get_worksheet()
    if ws is not None:
        try:
            records = ws.get_all_records(expected_headers=COLUMNS)
            return records
        except Exception:
            pass
    return _sqlite_latest(limit=10_000)


def latest_responses(limit: int = 5) -> list[dict[str, Any]]:
    rows = all_responses()
    return rows[-limit:][::-1] if rows else []


def is_admin(password: str) -> bool:
    if not password:
        return False
    try:
        expected = st.secrets["admin"]["password"]
    except Exception:
        expected = "shinhwa-admin"  # 기본값 (개발/임시용)
    return password == expected
