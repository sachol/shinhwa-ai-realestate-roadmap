"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성기 (v3)
- 면책 동의 → 설문(이메일 필수) → 로드맵 → PDF
- 공개 사이드바: 누적 응답 수만 노출 (개인정보 미노출)
- 관리자 모드: 사이드바 비밀번호 입력 시 전체 응답(상호/성함/이메일) 조회
- 저장소: Google Sheets 우선, 미설정 시 SQLite 폴백
"""
import re
import urllib.parse
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as components_html

# 1:1 컨설팅 문의 수신 메일 (CTA mailto 대상)
CONSULT_EMAIL = "sachol.cap@gmail.com"

# 카카오톡 공유 — 앱 배포 URL (공유 카드 링크 대상)
SHARE_APP_URL = "https://shinhwa-ai-realestate-roadmap-rsaaiforumfighting.streamlit.app"

# 카카오 공유 버튼 표시 토글 — 4019 인증 에러 디버깅 동안 임시 OFF
# 해결되면 True 로 되돌리면 즉시 부활됨
SHOW_KAKAO_SHARE = False

from storage import (
    init_storage,
    save_response,
    count_responses,
    latest_responses,
    all_responses,
    is_admin,
    is_admin_using_default,
    is_sheets_active,
)
from notify import send_admin_notification, send_student_pdf, is_notify_active
from roadmap_logic import (
    generate_roadmap,
    PROPERTY_OPTIONS,
    GOAL_OPTIONS,
    LEVEL_OPTIONS,
)
from pdf_export import build_pdf

init_storage()

st.set_page_config(
    page_title="신화AI부동산 | AI 학습 로드맵 진단",
    page_icon="🏠",
    layout="centered",
)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# ─────────────────────────────────────────────
# 글로벌 스타일
# ─────────────────────────────────────────────
PRIMARY = "#0F3D77"
ACCENT = "#FFB400"
BG_SOFT = "#F4F7FB"

st.markdown(
    f"""
    <style>
      @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

      :root {{
        --sh-primary:    {PRIMARY};
        --sh-primary-2:  #1B5BB0;
        --sh-accent:     {ACCENT};
        --sh-card-bg:    #FFFFFF;
        --sh-card-text:  #1B2330;
        --sh-section-bg: {BG_SOFT};
        --sh-section-fg: {PRIMARY};
        --sh-muted:      #8A95A6;
        --sh-shadow:     0 2px 10px rgba(15,61,119,0.06);
        --sh-hero-shadow:0 12px 32px rgba(15,61,119,0.22);
        --sh-warning:    #E04A4A;
        --sh-input-bg:   #FFFFFF;
        --sh-input-bd:   #DDE3EC;
        --sh-input-fg:   #1B2330;
      }}
      @media (prefers-color-scheme: dark) {{
        :root {{
          --sh-card-bg:    #1E2733;
          --sh-card-text:  #E8EEF7;
          --sh-section-bg: #1A2230;
          --sh-section-fg: #BFD3F0;
          --sh-muted:      #8E9BB0;
          --sh-shadow:     0 2px 10px rgba(0,0,0,0.35);
          --sh-hero-shadow:0 12px 32px rgba(0,0,0,0.55);
          --sh-warning:    #FF7575;
          --sh-input-bg:   #232C39;
          --sh-input-bd:   #2E3A4A;
          --sh-input-fg:   #E8EEF7;
        }}
      }}

      /* Pretendard 전역 적용 */
      html, body, .stApp, [class*="css"] {{
        font-family: 'Pretendard Variable', Pretendard, 'Apple SD Gothic Neo',
                     'Malgun Gothic', system-ui, -apple-system, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        letter-spacing: -0.01em;
      }}

      /* 부드러운 진입 애니메이션 */
      @keyframes shinhwa-fade-up {{
        0%   {{ opacity: 0; transform: translateY(8px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      .hero, .card, .shinhwa-cta-card, .section-head, .result-block, .chip-row {{
        animation: shinhwa-fade-up 0.45s ease both;
      }}

      /* 히어로 — 더 깊은 그라데이션 + 라이트 효과 */
      .hero {{
        position: relative;
        background:
          radial-gradient(ellipse at top left, rgba(255,180,0,0.22) 0%, transparent 45%),
          radial-gradient(ellipse at bottom right, rgba(255,255,255,0.15) 0%, transparent 50%),
          linear-gradient(135deg, var(--sh-primary) 0%, var(--sh-primary-2) 100%);
        color: #FFFFFF;
        border-radius: 18px;
        padding: 34px 28px;
        margin-bottom: 22px;
        box-shadow: var(--sh-hero-shadow);
        overflow: hidden;
      }}
      .hero::after {{
        content: '';
        position: absolute; right: -40px; bottom: -40px;
        width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(255,180,0,0.18) 0%, transparent 70%);
        pointer-events: none;
      }}
      .hero h1 {{
        color: #FFF !important; margin: 0 0 8px 0 !important;
        font-size: 2.05rem !important; font-weight: 800 !important;
        letter-spacing: -0.02em;
      }}
      .hero p  {{
        color: rgba(255,255,255,0.94); margin: 0;
        font-size: 1.02rem; line-height: 1.55;
      }}
      .hero .pill {{
        display:inline-block; background: var(--sh-accent); color:#0F3D77;
        padding: 5px 13px; border-radius: 999px; font-weight:800; font-size:0.78rem;
        margin-bottom: 12px; letter-spacing: 0.4px;
        box-shadow: 0 2px 8px rgba(255,180,0,0.35);
      }}

      /* 카드 */
      .card {{
        background: var(--sh-card-bg); color: var(--sh-card-text);
        border-radius: 14px; padding: 22px 24px; margin: 14px 0;
        box-shadow: var(--sh-shadow); border-left: 6px solid var(--sh-primary);
        transition: transform .15s ease, box-shadow .15s ease;
      }}
      .card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(15,61,119,0.10);
      }}
      .card.warning {{ border-left-color: var(--sh-warning); }}
      .card.accent  {{ border-left-color: var(--sh-accent); }}
      .card h3 {{ margin-top:0 !important; color: var(--sh-section-fg);
                 font-size: 1.18rem; font-weight: 800;
                 display:flex; align-items:center; gap:8px; }}
      .card ul, .card ol {{ margin: 10px 0 0 0; padding-left:22px; }}
      .card li {{ margin: 7px 0; line-height: 1.6; color: var(--sh-card-text); }}
      .card b  {{ color: var(--sh-card-text); font-weight: 700; }}

      /* 섹션 헤더 */
      .section-head {{
        display:flex; align-items:center; gap:12px;
        background: var(--sh-section-bg); padding: 12px 16px; border-radius: 12px;
        margin: 22px 0 12px 0; border-left: 4px solid var(--sh-primary);
      }}
      .section-head .badge {{
        background: linear-gradient(135deg, var(--sh-primary), var(--sh-primary-2));
        color:#FFF; width:28px; height:28px;
        border-radius: 50%; display:inline-flex; align-items:center; justify-content:center;
        font-weight: 800; font-size: 0.85rem;
        box-shadow: 0 2px 6px rgba(15,61,119,0.25);
      }}
      .section-head .label {{
        font-weight: 800; color: var(--sh-section-fg); font-size: 1.05rem;
        letter-spacing: -0.01em;
      }}

      /* 폼 입력 위젯 폴리시 */
      .stTextInput input, .stTextArea textarea,
      .stMultiSelect [data-baseweb="select"] > div,
      .stSelectbox [data-baseweb="select"] > div {{
        background: var(--sh-input-bg) !important;
        border-radius: 10px !important;
        border: 1.5px solid var(--sh-input-bd) !important;
        transition: border-color .15s ease, box-shadow .15s ease !important;
      }}
      .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--sh-primary) !important;
        box-shadow: 0 0 0 3px rgba(15,61,119,0.12) !important;
      }}
      .stTextInput label, .stTextArea label, .stMultiSelect label,
      .stSelectbox label, .stRadio label {{
        font-weight: 600 !important;
      }}

      /* 폼 제출 버튼 — 그라데이션 + 떠오르는 hover */
      .stFormSubmitButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--sh-primary) 0%, var(--sh-primary-2) 100%) !important;
        border: none !important;
        color:#FFF !important;
        height: 54px !important;
        font-size: 1.02rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 16px rgba(15,61,119,0.28) !important;
        transition: transform .12s ease, box-shadow .15s ease !important;
      }}
      .stFormSubmitButton > button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(15,61,119,0.38) !important;
      }}
      /* 일반 버튼·다운로드 버튼은 기존 유지 + 살짝 폴리시 */
      .stButton > button[kind="primary"],
      .stDownloadButton > button[kind="primary"] {{
        background: var(--sh-primary) !important; border:none !important;
        color:#FFF !important; height:48px; font-weight:700;
        border-radius: 10px !important;
        transition: transform .12s ease, box-shadow .15s ease !important;
      }}
      .stButton > button[kind="primary"]:hover,
      .stDownloadButton > button[kind="primary"]:hover {{
        background:#0a2c5a !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(15,61,119,0.25) !important;
      }}

      /* 결과 영역의 칩(chip) 배지 */
      .chip-row {{
        display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 4px 0;
      }}
      .chip {{
        display: inline-flex; align-items: center; gap: 6px;
        background: var(--sh-section-bg);
        color: var(--sh-section-fg);
        border: 1px solid rgba(15,61,119,0.18);
        padding: 6px 12px; border-radius: 999px;
        font-size: 0.85rem; font-weight: 600;
        line-height: 1.4;
      }}
      .chip.accent {{
        background: rgba(255,180,0,0.16);
        color: #8A5A00;
        border-color: rgba(255,180,0,0.45);
      }}
      @media (prefers-color-scheme: dark) {{
        .chip.accent {{ color:#FFD66A; }}
      }}
      .chip-label {{
        font-size: 0.78rem; font-weight: 700; color: var(--sh-muted);
        margin-bottom: 4px; letter-spacing: 0.02em;
        text-transform: uppercase;
      }}

      .footer {{ text-align:center; color: var(--sh-muted); font-size:0.82rem; margin-top:24px; }}

      /* 모바일 폭에서 패딩·폰트 조정 */
      @media (max-width: 640px) {{
        .hero {{ padding: 26px 20px; border-radius: 14px; }}
        .hero h1 {{ font-size: 1.65rem !important; }}
        .card {{ padding: 18px 18px; }}
        .stFormSubmitButton > button[kind="primary"] {{ height: 50px !important; font-size: 0.98rem !important; }}
      }}

      /* 카카오톡 공유 카드 — 동료 중개사 추천 (앱 홍보 CTA) */
      .shinhwa-share-card {{
        margin: 22px 0 6px 0;
        padding: 22px 22px 8px 22px;
        background: linear-gradient(135deg, #FFFDF1 0%, #FFF6C9 100%);
        border-left: 6px solid #FEE500;
        border-radius: 14px;
        box-shadow: 0 3px 10px rgba(254,229,0,0.18);
      }}
      .shinhwa-share-card .share-pill {{
        display:inline-block; background:#3C1E1E; color:#FEE500;
        font-size:11px; font-weight:700; letter-spacing:.4px;
        padding:4px 10px; border-radius:999px; margin-bottom:10px;
      }}
      .shinhwa-share-card h3 {{
        margin:6px 0 4px 0 !important;
        color:#0F3D77 !important;
        font-size:1.2rem !important;
      }}
      .shinhwa-share-card p,
      .shinhwa-share-card p b {{
        color:#3A4250 !important;
      }}

      /* 1:1 컨설팅 CTA 카드 + 버튼 (어떤 테마에서도 가독성 보장) */
      .shinhwa-cta-card {{
        margin: 26px 0 10px 0;
        padding: 24px 22px;
        background: linear-gradient(135deg, #FFF7DE 0%, #FFE9A8 100%);
        border-left: 6px solid {ACCENT};
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(255,180,0,0.18);
      }}
      .shinhwa-cta-card .pill {{
        display:inline-block; background:{PRIMARY}; color:#FFFFFF;
        font-size:11px; font-weight:700; letter-spacing:.4px;
        padding:4px 10px; border-radius:999px; margin-bottom:10px;
      }}
      .shinhwa-cta-card h3 {{
        margin:6px 0 4px 0 !important;
        color:#0F3D77 !important;
        font-size:1.25rem !important;
      }}
      .shinhwa-cta-card p,
      .shinhwa-cta-card p b {{
        color:#3A4250 !important;
      }}
      .shinhwa-cta-card .cta-hint {{
        color:#6B7686 !important;
        font-size:11.5px;
        line-height:1.5;
        margin-top:14px;
      }}

      /* 컨설팅 버튼 — Streamlit anchor 기본 스타일을 강하게 덮어쓰기 */
      a.shinhwa-cta-btn,
      a.shinhwa-cta-btn:link,
      a.shinhwa-cta-btn:visited,
      a.shinhwa-cta-btn:hover,
      a.shinhwa-cta-btn:active,
      .stMarkdown a.shinhwa-cta-btn,
      .stMarkdown a.shinhwa-cta-btn:visited {{
        display: inline-block !important;
        background: #FFFFFF !important;
        color: #0F3D77 !important;
        text-decoration: none !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 13px 24px !important;
        border-radius: 10px !important;
        border: 2px solid #0F3D77 !important;
        box-shadow: 0 4px 12px rgba(15,61,119,0.18) !important;
        transition: transform .08s ease, box-shadow .15s ease, background .15s ease !important;
      }}
      a.shinhwa-cta-btn:hover {{
        background: #0F3D77 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(15,61,119,0.28) !important;
      }}
      a.shinhwa-cta-btn span.btn-text {{
        color: inherit !important;
      }}
      /* Primary 액션 (Gmail) — 채워진 네이비 */
      a.shinhwa-cta-btn-primary,
      a.shinhwa-cta-btn-primary:link,
      a.shinhwa-cta-btn-primary:visited,
      .stMarkdown a.shinhwa-cta-btn-primary {{
        background: #0F3D77 !important;
        color: #FFFFFF !important;
        border-color: #0F3D77 !important;
      }}
      a.shinhwa-cta-btn-primary:hover {{
        background: #0a2c5a !important;
        color: #FFFFFF !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title: str, subtitle: str, pill: str | None = None) -> None:
    pill_html = f'<span class="pill">{pill}</span><br>' if pill else ""
    st.markdown(
        f"""<div class="hero">{pill_html}<h1>🏠 {title}</h1><p>{subtitle}</p></div>""",
        unsafe_allow_html=True,
    )


def section_head(badge: str, label: str) -> None:
    st.markdown(
        f"""<div class="section-head">
            <span class="badge">{badge}</span>
            <span class="label">{label}</span>
        </div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# 관리자 통계 헬퍼
# ─────────────────────────────────────────────
_LEVEL_NUM_RE = re.compile(r"^\s*(\d+)")


def _split_multivalue(value) -> list[str]:
    """저장소가 SQLite(list) / Sheets(콤마 문자열) 어느 쪽이든 안전하게 list로 변환."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    if not s:
        return []
    # JSON 리스트로 저장된 경우도 처리
    if s.startswith("[") and s.endswith("]"):
        import json
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass
    return [p.strip() for p in s.split(",") if p.strip()]


def _level_to_number(level_str: str) -> int | None:
    if not level_str:
        return None
    m = _LEVEL_NUM_RE.match(str(level_str))
    return int(m.group(1)) if m else None


OWNER_EMAILS: tuple[str, ...] = ("sachol.cap@gmail.com", "sachol@kakao.com")
TEST_KEYWORDS: tuple[str, ...] = ("TEST", "테스트", "알림테스트", "홍길동")

# ── 강의반 자동 분류 (2026-05-26) ──────────────────────────────
# 숙련도 5단계 → 3개 강의반으로 묶음 (현재 14명 unique 분포에 맞춰 설계)
CLASS_INTRO = "AI 입문반"            # Lv 1~2 (입문 + 기초 ChatGPT)
CLASS_BASIC = "AI 기본 활용반"       # Lv 3   (업무에 ChatGPT 활용 중)
CLASS_ADVANCED = "AI 심화 자동화반"  # Lv 4~5 (능숙·전문가)
CLASS_UNCLASSIFIED = "분류 불가"

# 매물 트랙 (보조 컬럼) — 강의 콘텐츠 매칭용
TRACK_APT = "아파트 트랙"           # 아파트·오피스텔 위주
TRACK_NON_APT = "비아파트 트랙"     # 토지·상가·재개발 등
TRACK_MIXED = "혼합 트랙"           # 둘 다
TRACK_UNKNOWN = "미분류"

APARTMENT_PROPERTIES: frozenset[str] = frozenset({"아파트", "오피스텔"})


def classify_main_class(ai_level: str) -> str:
    """숙련도 문자열에서 추천 강의반을 반환.

    Args:
        ai_level: 응답 시트의 ai_level 컬럼 값 (예: "2. 기초 — ChatGPT 사용").

    Returns:
        CLASS_INTRO / CLASS_BASIC / CLASS_ADVANCED / CLASS_UNCLASSIFIED.
    """
    level_num = _level_to_number(ai_level)
    if level_num is None:
        return CLASS_UNCLASSIFIED
    if level_num <= 2:
        return CLASS_INTRO
    if level_num == 3:
        return CLASS_BASIC
    if level_num >= 4:
        return CLASS_ADVANCED
    return CLASS_UNCLASSIFIED


def find_previous_responses(email: str, all_rows: list[dict]) -> list[dict]:
    """같은 이메일의 이전 응답을 최근 → 오래된 순으로 반환.

    Args:
        email: 검색 대상 이메일 (대소문자·공백 무시).
        all_rows: 전체 응답 리스트 (보통 all_responses() 의 결과).

    Returns:
        같은 이메일의 응답 리스트 (없으면 빈 리스트). 0번째가 가장 최근.
    """
    if not email:
        return []
    target = email.lower().strip()
    matches = [
        r for r in all_rows
        if str(r.get("email") or "").lower().strip() == target
    ]
    if not matches:
        return []
    parsed_dts = pd.to_datetime(
        [r.get("submitted_at") for r in matches], errors="coerce"
    )
    pairs = list(zip(parsed_dts, matches))
    pairs.sort(
        key=lambda p: p[0] if pd.notna(p[0]) else pd.Timestamp.min,
        reverse=True,
    )
    return [r for _, r in pairs]


def build_comparison(current: dict, previous: dict) -> dict:
    """현재 응답과 직전 응답을 비교한 리포트 dict 반환.

    Args:
        current: 방금 제출된 응답 (save_response 직전 payload 형태).
        previous: 같은 이메일의 직전 응답 (시트 row).

    Returns:
        {
          "days_between": int | None,
          "level": {"prev": int|None, "current": int|None, "delta": int|None,
                    "prev_label": str, "current_label": str},
          "properties": {"added": list[str], "removed": list[str], "kept": list[str]},
          "goals": {"added": list[str], "removed": list[str], "kept": list[str]},
        }
    """
    # 시간 간격
    cur_dt = pd.to_datetime(current.get("submitted_at"), errors="coerce")
    prev_dt = pd.to_datetime(previous.get("submitted_at"), errors="coerce")
    days_between: int | None = None
    if pd.notna(cur_dt) and pd.notna(prev_dt):
        days_between = max(0, (cur_dt - prev_dt).days)

    # 숙련도
    cur_lv = _level_to_number(current.get("ai_level"))
    prev_lv = _level_to_number(previous.get("ai_level"))
    level_delta: int | None = None
    if cur_lv is not None and prev_lv is not None:
        level_delta = cur_lv - prev_lv

    # 매물·목표는 집합 연산. 입력 순서 보존을 위해 list 로 변환.
    cur_props = _split_multivalue(current.get("main_property"))
    prev_props = _split_multivalue(previous.get("main_property"))
    cur_props_set, prev_props_set = set(cur_props), set(prev_props)

    cur_goals = _split_multivalue(current.get("ai_goals"))
    prev_goals = _split_multivalue(previous.get("ai_goals"))
    cur_goals_set, prev_goals_set = set(cur_goals), set(prev_goals)

    return {
        "days_between": days_between,
        "level": {
            "prev": prev_lv,
            "current": cur_lv,
            "delta": level_delta,
            "prev_label": str(previous.get("ai_level") or "").strip(),
            "current_label": str(current.get("ai_level") or "").strip(),
        },
        "properties": {
            "added": [p for p in cur_props if p not in prev_props_set],
            "removed": [p for p in prev_props if p not in cur_props_set],
            "kept": [p for p in cur_props if p in prev_props_set],
        },
        "goals": {
            "added": [g for g in cur_goals if g not in prev_goals_set],
            "removed": [g for g in prev_goals if g not in cur_goals_set],
            "kept": [g for g in cur_goals if g in prev_goals_set],
        },
    }


def classify_property_track(main_property) -> str:
    """주력 매물 (list 또는 콤마 문자열) 에서 매물 트랙을 반환.

    Args:
        main_property: 시트의 main_property 컬럼 (SQLite list 또는 콤마 문자열).

    Returns:
        TRACK_APT / TRACK_NON_APT / TRACK_MIXED / TRACK_UNKNOWN.
    """
    props = _split_multivalue(main_property)
    if not props:
        return TRACK_UNKNOWN
    has_apt = any(p in APARTMENT_PROPERTIES for p in props)
    has_non_apt = any(p not in APARTMENT_PROPERTIES for p in props)
    if has_apt and has_non_apt:
        return TRACK_MIXED
    if has_apt:
        return TRACK_APT
    if has_non_apt:
        return TRACK_NON_APT
    return TRACK_UNKNOWN


def _filter_rows(
    rows: list[dict],
    *,
    exclude_test: bool = True,
    exclude_duplicates: bool = True,
    exclude_owner: bool = False,
) -> tuple[list[dict], dict]:
    """관리자 통계용 응답 필터링.

    Args:
        rows: 시트/DB에서 받은 원본 응답 list.
        exclude_test: TEST 키워드(business_name·user_name)가 포함된 행 제외.
        exclude_duplicates: 같은 이메일의 중복 응답을 가장 최근 1건만 남김.
        exclude_owner: OWNER_EMAILS 에 등록된 이메일 응답 제외.

    Returns:
        (filtered, stats) — stats 는 {"test": n, "duplicate": n, "owner": n} 형태의 제거 건수.
    """
    excluded = {"test": 0, "duplicate": 0, "owner": 0}
    working = list(rows)

    if exclude_test:
        kept = []
        for r in working:
            biz = str(r.get("business_name") or "").upper()
            usr = str(r.get("user_name") or "").upper()
            if any(kw.upper() in biz or kw.upper() in usr for kw in TEST_KEYWORDS):
                excluded["test"] += 1
            else:
                kept.append(r)
        working = kept

    if exclude_owner:
        owner_set = {e.lower() for e in OWNER_EMAILS}
        kept = []
        for r in working:
            email = str(r.get("email") or "").lower().strip()
            if email in owner_set:
                excluded["owner"] += 1
            else:
                kept.append(r)
        working = kept

    if exclude_duplicates:
        # datetime 파싱으로 robust 정렬 (hour zero-pad 누락 케이스 대응)
        # 최신 응답이 먼저 오게 정렬 → 처음 본 이메일만 유지 → 최신 1건만 남김
        parsed_dts = pd.to_datetime(
            [r.get("submitted_at") for r in working], errors="coerce"
        )
        pairs = list(zip(parsed_dts, working))
        pairs.sort(
            key=lambda p: p[0] if pd.notna(p[0]) else pd.Timestamp.min,
            reverse=True,
        )
        seen_emails: set[str] = set()
        kept_pairs: list = []
        for dt, r in pairs:
            email = str(r.get("email") or "").lower().strip()
            if email and email in seen_emails:
                excluded["duplicate"] += 1
                continue
            if email:
                seen_emails.add(email)
            kept_pairs.append((dt, r))
        # 원래 시간 오름차순 복원 (UI/CSV 출력 일관성)
        kept_pairs.sort(key=lambda p: p[0] if pd.notna(p[0]) else pd.Timestamp.min)
        working = [r for _, r in kept_pairs]

    return working, excluded


def render_admin_dashboard(rows: list[dict]) -> None:
    """관리자 대시보드 — KPI 4타일 + 4개 차트."""
    if not rows:
        st.info("아직 응답이 없습니다. 진단이 1건이라도 쌓이면 통계가 표시됩니다.")
        return

    df = pd.DataFrame(rows)

    # ── 다중값 컬럼 정규화 ──
    df["_props"] = df.get("main_property", "").apply(_split_multivalue)
    df["_goals"] = df.get("ai_goals", "").apply(_split_multivalue)
    df["_level_num"] = df.get("ai_level", "").apply(_level_to_number)
    df["_submitted_dt"] = pd.to_datetime(
        df.get("submitted_at", ""), errors="coerce"
    )
    # 강의반·매물 트랙 자동 분류
    df["_main_class"] = df.get("ai_level", "").apply(classify_main_class)
    df["_property_track"] = df.get("main_property", "").apply(classify_property_track)

    # ── KPI 계산 ──
    total = len(df)
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    recent_week = int((df["_submitted_dt"] >= week_ago).sum())

    avg_level = df["_level_num"].dropna().mean()
    avg_level_str = f"{avg_level:.1f} / 5" if pd.notna(avg_level) else "—"

    all_props = [p for lst in df["_props"] for p in lst]
    top_property = Counter(all_props).most_common(1)
    top_prop_label = top_property[0][0] if top_property else "—"

    class_counts = df["_main_class"].value_counts()
    intro_n = int(class_counts.get(CLASS_INTRO, 0))
    basic_n = int(class_counts.get(CLASS_BASIC, 0))
    advanced_n = int(class_counts.get(CLASS_ADVANCED, 0))

    # ── KPI 타일 ──
    st.markdown("### 📊 핵심 지표")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총 응답", f"{total:,} 건")
    k2.metric("최근 7일", f"{recent_week:,} 건")
    k3.metric("평균 숙련도", avg_level_str)
    k4.metric("Top 매물", top_prop_label)

    # ── 강의반 KPI 타일 (강사 배정 의사결정용) ──
    st.markdown("#### 🎓 추천 강의반 분포")
    g1, g2, g3 = st.columns(3)
    g1.metric(CLASS_INTRO, f"{intro_n:,} 명")
    g2.metric(CLASS_BASIC, f"{basic_n:,} 명")
    g3.metric(CLASS_ADVANCED, f"{advanced_n:,} 명")

    st.divider()

    # ── 차트 행: 매물 분포 + AI 목표 분포 ──
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🏠 주력 매물 분포 (복수응답)")
        prop_counts = Counter(all_props)
        if prop_counts:
            prop_df = pd.DataFrame(
                prop_counts.most_common(),
                columns=["매물", "응답 수"],
            ).set_index("매물")
            st.bar_chart(prop_df, height=320, color="#0F3D77")
        else:
            st.caption("_(데이터 부족)_")

    with c2:
        st.markdown("#### 🎯 AI 활용 목표 Top (복수응답)")
        all_goals = [g for lst in df["_goals"] for g in lst]
        goal_counts = Counter(all_goals)
        if goal_counts:
            goal_df = pd.DataFrame(
                goal_counts.most_common(10),
                columns=["목표", "응답 수"],
            ).set_index("목표")
            st.bar_chart(goal_df, height=320, color="#FFB400")
        else:
            st.caption("_(데이터 부족)_")

    st.divider()

    # ── 차트 행: 숙련도 분포 + 일별 추이 ──
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### 📚 AI 숙련도 분포")
        level_series = df["ai_level"].dropna()
        level_series = level_series[level_series.str.strip() != ""]
        if not level_series.empty:
            level_df = (
                level_series.value_counts()
                .rename_axis("숙련도")
                .reset_index(name="응답 수")
                .sort_values("숙련도")
                .set_index("숙련도")
            )
            st.bar_chart(level_df, height=320, color="#1B5BB0")
        else:
            st.caption("_(데이터 부족)_")

    with c4:
        st.markdown("#### 📈 일별 응답 추이")
        dt_series = df["_submitted_dt"].dropna()
        if not dt_series.empty:
            daily = (
                dt_series.dt.floor("D")
                .value_counts()
                .sort_index()
                .rename_axis("날짜")
                .reset_index(name="응답 수")
                .set_index("날짜")
            )
            st.line_chart(daily, height=320, color="#0F3D77")
        else:
            st.caption("_(데이터 부족)_")

    st.divider()

    # ── 차트 행: 강의반 분포 + 매물 트랙 분포 ──
    c5, c6 = st.columns(2)
    with c5:
        st.markdown("#### 🎓 추천 강의반 분포")
        class_ordered = [CLASS_INTRO, CLASS_BASIC, CLASS_ADVANCED]
        class_series = df["_main_class"]
        class_df_data = [
            (name, int((class_series == name).sum())) for name in class_ordered
        ]
        # 분류 불가도 1개 이상이면 추가
        unclassified_n = int((class_series == CLASS_UNCLASSIFIED).sum())
        if unclassified_n > 0:
            class_df_data.append((CLASS_UNCLASSIFIED, unclassified_n))
        class_df = pd.DataFrame(class_df_data, columns=["강의반", "인원"]).set_index("강의반")
        st.bar_chart(class_df, height=320, color="#FFB400")

    with c6:
        st.markdown("#### 🏘️ 매물 트랙 분포")
        track_ordered = [TRACK_APT, TRACK_NON_APT, TRACK_MIXED]
        track_series = df["_property_track"]
        track_df_data = [
            (name, int((track_series == name).sum())) for name in track_ordered
        ]
        unknown_n = int((track_series == TRACK_UNKNOWN).sum())
        if unknown_n > 0:
            track_df_data.append((TRACK_UNKNOWN, unknown_n))
        track_df = pd.DataFrame(track_df_data, columns=["트랙", "인원"]).set_index("트랙")
        st.bar_chart(track_df, height=320, color="#0F3D77")

    st.divider()


def _build_consult_message(
    business_name: str,
    user_name: str,
    email: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> tuple[str, str]:
    """1:1 컨설팅 문의 메일의 (제목, 본문)을 반환.
    본문은 URL 길이 제한을 고려해 핵심만 간결하게 작성."""
    subject = f"[신화AI부동산] 1:1 컨설팅 문의 — {business_name} / {user_name}"

    props = ", ".join(main_property) if main_property else "(없음)"
    if custom_property:
        props += f" / {custom_property}"
    goals = ", ".join(ai_goals) if ai_goals else "(없음)"
    if custom_goals:
        goals += f" / {custom_goals}"

    body = (
        f"안녕하세요, 신화 대표님.\n\n"
        f"신화AI부동산 진단을 받은 {business_name}의 {user_name}입니다.\n"
        f"1:1 맞춤 컨설팅을 받아보고 싶습니다.\n\n"
        f"■ 제 진단 요약\n"
        f"· 사업자 상호: {business_name}\n"
        f"· 이메일: {email}\n"
        f"· AI 숙련도: {ai_level}\n"
        f"· 주력 매물: {props}\n"
        f"· AI 관심 업무: {goals}\n\n"
        f"■ 컨설팅에서 다루고 싶은 내용\n"
        f"(자유롭게 작성)\n\n"
        f"■ 희망 일정 / 연락 가능 시간\n"
        f"(편하신 시간대 알려주세요)\n\n"
        f"감사합니다.\n{user_name} 드림"
    )
    return subject, body


def _build_gmail_url(subject: str, body: str) -> str:
    """Gmail 웹 컴포즈 URL (어떤 OS·브라우저에서도 작동)."""
    enc_subject = urllib.parse.quote(subject)
    enc_body = urllib.parse.quote(body)
    return (
        f"https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={CONSULT_EMAIL}&su={enc_subject}&body={enc_body}"
    )


def render_comparison_card(comparison: dict, total_visits: int) -> None:
    """결과 페이지 상단의 '이전 진단과 비교' 카드를 렌더링.

    Args:
        comparison: build_comparison() 의 반환값.
        total_visits: 같은 이메일의 누적 진단 횟수 (현재 포함).
    """
    level = comparison["level"]
    days = comparison["days_between"]
    delta = level.get("delta")

    # 헤드라인 — 가장 강한 시그널 우선 (숙련도 변화 > 매물 추가 > 목표 추가)
    if delta is not None and delta > 0:
        headline = f"🎉 한 단계씩 성장 중! 숙련도 **{delta}단계 상승**하셨습니다."
        accent = "#16A34A"   # green
    elif delta is not None and delta < 0:
        headline = "🔁 다시 한 번 차근차근 — 직전보다 숙련도 응답을 보수적으로 잡으셨네요."
        accent = "#0F3D77"   # primary
    else:
        headline = "🔁 꾸준히 진단받고 계시네요. 변화 흐름을 같이 살펴보세요."
        accent = "#0F3D77"

    sub = []
    if days is not None:
        sub.append(f"직전 진단으로부터 **{days}일** 경과")
    sub.append(f"이 이메일로 **{total_visits}번째** 진단")
    sub_line = " · ".join(sub)

    st.markdown(
        f"""
        <div class="card accent" style="border-left-color:{accent};">
          <h3 style="color:{accent};">{headline}</h3>
          <p style="margin:0 0 6px 0; color:var(--sh-muted);">{sub_line}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 변화 디테일 (숙련도·매물·목표) ──
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### 📚 숙련도")
        prev_lbl = level.get("prev_label") or "(이전 기록 없음)"
        cur_lbl = level.get("current_label") or "(현재 기록 없음)"
        if delta is None:
            st.caption("비교 가능한 숫자 정보가 없습니다.")
        elif delta > 0:
            st.success(f"▲ +{delta}단계")
        elif delta < 0:
            st.warning(f"▼ {delta}단계")
        else:
            st.info("동일 단계 유지")
        st.caption(f"이전: {prev_lbl}")
        st.caption(f"현재: {cur_lbl}")

    with col2:
        st.markdown("##### 🏠 주력 매물 변화")
        props = comparison["properties"]
        if props["added"]:
            st.success("**+ 추가**: " + ", ".join(props["added"]))
        if props["removed"]:
            st.caption("**− 제외**: " + ", ".join(props["removed"]))
        if not props["added"] and not props["removed"]:
            st.info(f"동일 유지 ({len(props['kept'])}종)")

    with col3:
        st.markdown("##### 🎯 AI 활용 목표 변화")
        goals = comparison["goals"]
        if goals["added"]:
            st.success("**+ 추가**: " + ", ".join(goals["added"]))
        if goals["removed"]:
            st.caption("**− 제외**: " + ", ".join(goals["removed"]))
        if not goals["added"] and not goals["removed"]:
            st.info(f"동일 유지 ({len(goals['kept'])}종)")


def render_selection_chips(
    business_name: str,
    user_name: str,
    ai_level: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
) -> None:
    """선택한 항목들을 시각적 칩 배지로 표시 (로드맵 텍스트 위)."""
    def _chips(items: list[str], extra: str = "", accent: bool = False) -> str:
        cls = "chip accent" if accent else "chip"
        html = ""
        for it in items:
            html += f'<span class="{cls}">{it}</span>'
        if extra:
            html += f'<span class="{cls}">+ {extra}</span>'
        return html or '<span class="chip" style="opacity:.5;">(없음)</span>'

    st.markdown(
        f"""
        <div class="result-block" style="
            background: var(--sh-card-bg);
            border-radius: 14px;
            padding: 22px 24px;
            margin: 14px 0;
            box-shadow: var(--sh-shadow);
            border-left: 6px solid var(--sh-accent);">
          <div style="display:flex; flex-wrap:wrap; gap:18px;
                      align-items:baseline; margin-bottom:12px;">
            <div>
              <div class="chip-label">진단 대상</div>
              <div style="font-size:1.1rem; font-weight:800; color: var(--sh-card-text);">
                {business_name} · {user_name} 공인중개사님
              </div>
            </div>
            <div style="margin-left:auto;">
              <div class="chip-label">AI 숙련도</div>
              <span class="chip accent">{ai_level}</span>
            </div>
          </div>

          <div class="chip-label">주력 매물·업무</div>
          <div class="chip-row">{_chips(main_property, custom_property)}</div>

          <div class="chip-label" style="margin-top:12px;">AI 활용 목표</div>
          <div class="chip-row">{_chips(ai_goals, custom_goals, accent=True)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kakao_share_button() -> None:
    """카카오톡 공유 버튼 — 동료 중개사 추천용 (앱 홍보 컨셉).
    Kakao SDK v2 (Share.sendDefault, objectType='text')를 사용해
    이미지 없이 텍스트+버튼만 있는 공유 카드를 즉시 발송한다.
    JavaScript 키가 secrets에 없으면 렌더링을 건너뛴다.
    SHOW_KAKAO_SHARE 토글이 False 이면 즉시 종료한다.
    """
    if not SHOW_KAKAO_SHARE:
        return
    js_key = st.secrets.get("kakao", {}).get("javascript_key", "")
    if not js_key:
        return

    share_text = (
        "공인중개사 전용 AI 학습 진단\n\n"
        "주력 매물·숙련도 1분 입력 → 맞춤 AI 학습 로드맵 자동 생성.\n"
        "신화AI부동산 제공."
    )
    # JS 문자열 리터럴 안에서 줄바꿈은 \n 으로 이스케이프
    share_text_js = share_text.replace("\\", "\\\\").replace("\n", "\\n").replace("'", "\\'")

    st.markdown(
        """
        <div class="shinhwa-share-card">
          <span class="share-pill">💬 동료 중개사에게도 추천</span>
          <h3>이 진단, 동료 중개사에게도 알려주세요</h3>
          <p style="margin:0 0 14px 0; font-size:0.95rem; line-height:1.6;">
            한 분이라도 더 <b>AI로 시간 절약</b>하실 수 있도록,<br>
            <b>카카오톡 1번 클릭</b>으로 공유해보세요.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    components_html(
        f"""
        <div style="text-align:center; padding:6px 0 12px 0;">
          <button id="shinhwa-kakao-share-btn"
            style="
              background:#FEE500; color:#191600;
              border:none; border-radius:12px;
              padding:14px 28px; font-size:1.0rem; font-weight:700;
              cursor:pointer; box-shadow:0 4px 14px rgba(254,229,0,0.35);
              transition:transform .12s ease, box-shadow .12s ease;
              font-family:'Pretendard','Apple SD Gothic Neo','Noto Sans KR',sans-serif;
            "
            onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 6px 18px rgba(254,229,0,0.45)';"
            onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 14px rgba(254,229,0,0.35)';"
          >
            💬 카카오톡으로 동료 중개사에게 추천하기
          </button>
          <p style="margin:10px 0 0 0; font-size:0.82rem; color:#6B7280;">
            새 창에서 카카오톡 메시지함이 열립니다.
          </p>
        </div>
        <script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.4/kakao.min.js"></script>
        <script>
          (function() {{
            try {{
              if (typeof Kakao === 'undefined') return;
              if (!Kakao.isInitialized()) Kakao.init('{js_key}');
              var btn = document.getElementById('shinhwa-kakao-share-btn');
              if (!btn) return;
              btn.addEventListener('click', function() {{
                Kakao.Share.sendDefault({{
                  objectType: 'text',
                  text: '{share_text_js}',
                  link: {{
                    mobileWebUrl: '{SHARE_APP_URL}',
                    webUrl: '{SHARE_APP_URL}'
                  }},
                  buttonTitle: '지금 무료 진단 받기'
                }});
              }});
            }} catch (e) {{
              console.error('Kakao share init failed:', e);
            }}
          }})();
        </script>
        """,
        height=160,
    )


def consulting_cta(gmail_url: str, subject: str, body: str) -> None:
    """결과 페이지 하단의 1:1 컨설팅 신청 CTA 카드.
    Gmail 웹 작성 버튼 + 다른 메일/메신저 사용자를 위한 복사 섹션."""
    st.markdown(
        f"""
        <div class="shinhwa-cta-card">
          <span class="pill">⭐ 수강생 전용 한정 혜택</span>
          <h3>더 깊은 1:1 맞춤 컨설팅이 필요하신가요?</h3>
          <p style="margin:0 0 18px 0; font-size:0.95rem; line-height:1.6;">
            진단 결과를 바탕으로 <b>주력 매물·고객층·업무 환경</b>에 꼭 맞는
            AI 자동화 설계를 받아보실 수 있습니다.<br>
            <b>수강생분께만</b> 신화AI부동산의 노하우와 시간을 우선 배정해드립니다.
          </p>
          <a href="{gmail_url}" target="_blank" rel="noopener"
             class="shinhwa-cta-btn shinhwa-cta-btn-primary">
            <span class="btn-text">🌐 Gmail로 컨설팅 문의 작성하기</span>
          </a>
          <p class="cta-hint">
            💡 새 탭에서 Gmail 작성창이 열립니다.
            <b style="color:#3A4250 !important;">받는 사람·제목·본문이 자동으로 채워져</b> 있어
            희망 일정과 다루고 싶은 주제만 추가하시면 됩니다.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Naver/Daum/카톡 등 Gmail 외 사용자를 위한 복사 섹션
    with st.expander("✉️ Gmail 대신 Naver·Daum·카톡 등으로 보내시려면 (내용 복사하기)"):
        st.caption("받는 사람")
        st.code(CONSULT_EMAIL, language="text")
        st.caption("제목")
        st.code(subject, language="text")
        st.caption("본문")
        st.code(body, language="text")
        st.info(
            "각 영역 우측 상단의 **📋 복사 아이콘**을 눌러 복사하실 수 있습니다.\n\n"
            "복사한 내용을 평소 사용하시는 **Naver·Daum 메일이나 카카오톡**에 그대로 붙여넣어 보내주세요."
        )


# ─────────────────────────────────────────────
# 사이드바 — 공개: 카운트만 / 관리자: 비밀번호로 전체 조회
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h3 style='color:{PRIMARY};margin-top:0;'>🏠 신화AI부동산</h3>", unsafe_allow_html=True)
    st.caption("공인중개사 AI 학습 진단")
    st.metric(label="누적 진단 응답", value=f"{count_responses():,} 건")
    storage_label = "Google Sheets" if is_sheets_active() else "로컬 SQLite"
    notify_label = "ON" if is_notify_active() else "OFF"
    st.caption(f"📦 저장소: **{storage_label}** · ✉️ 알림: **{notify_label}**")

    st.divider()
    st.markdown("##### 🔐 관리자 모드")

    # "관리자 모드 종료" 클릭 직후엔 비밀번호 위젯 렌더링 전에 키를 삭제해야 함
    if st.session_state.pop("_admin_logout_request", False):
        st.session_state.pop("admin_pw_input", None)

    admin_pw = st.text_input(
        "관리자 비밀번호",
        type="password",
        placeholder="비밀번호 입력 후 Enter",
        key="admin_pw_input",
    )
    is_admin_user = is_admin(admin_pw)
    if admin_pw and not is_admin_user:
        st.error("비밀번호가 올바르지 않습니다.")
    if is_admin_user:
        st.success("✅ 관리자 인증됨")
        if st.button("🚪 관리자 모드 종료", use_container_width=True, key="admin_logout_btn"):
            # 다음 런에서 비밀번호 위젯을 초기화하도록 신호만 남기고 즉시 재실행
            st.session_state["_admin_logout_request"] = True
            st.rerun()
    if is_admin_using_default():
        st.info("💡 기본 비밀번호 사용 중: **shinhwa-admin**\n\n배포 전 `.streamlit/secrets.toml`에서 변경하세요.")

    if st.session_state.get("consented"):
        st.divider()
        if st.button("🔄 처음부터 다시", use_container_width=True):
            for k in ("consented",):
                st.session_state.pop(k, None)
            st.rerun()

# ─────────────────────────────────────────────
# 관리자 모드 — 전체 응답 테이블
# ─────────────────────────────────────────────
if is_admin_user:
    hero(
        title="관리자 대시보드",
        subtitle="모든 응답을 조회하고 통계를 확인할 수 있습니다.",
        pill="ADMIN",
    )

    rows = all_responses()

    # ── 통계 필터 옵션 (체크 시 즉시 KPI·차트·테이블·CSV 모두 반영) ──
    with st.expander("🔍 통계 필터 옵션", expanded=False):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            f_test = st.checkbox(
                "TEST 응답 제외",
                value=True,
                help="business_name 또는 user_name 에 'TEST'·'테스트'·'홍길동' 등이 포함된 행 제외",
            )
        with f_col2:
            f_dup = st.checkbox(
                "중복 응답 제외 (이메일 기준 최신만)",
                value=True,
                help="같은 이메일이 여러 번 제출된 경우, 가장 최근 응답 1건만 통계에 반영",
            )
        with f_col3:
            f_owner = st.checkbox(
                "대표님 본인 응답 제외",
                value=False,
                help="sachol.cap@gmail.com / sachol@kakao.com 응답 제외 (시연·검증 응답 분리)",
            )

    filtered_rows, excluded_stats = _filter_rows(
        rows,
        exclude_test=f_test,
        exclude_duplicates=f_dup,
        exclude_owner=f_owner,
    )

    total_excluded = sum(excluded_stats.values())
    if total_excluded > 0:
        st.caption(
            f"🔍 원본 {len(rows)}건 → 필터 후 **{len(filtered_rows)}건** "
            f"(TEST {excluded_stats['test']}건 · 중복 {excluded_stats['duplicate']}건 · 본인 {excluded_stats['owner']}건 제외)"
        )

    # 통계 위젯 (필터된 데이터 기준)
    render_admin_dashboard(filtered_rows)

    # 전체 응답 테이블 (필터된 데이터 기준)
    st.markdown(f"### 📋 전체 응답 ({len(filtered_rows)}건)")
    if not filtered_rows:
        st.info("필터 조건을 만족하는 응답이 없습니다.")
    else:
        df = pd.DataFrame(filtered_rows)
        # 자동 분류 컬럼 추가 (강사 강의반 배정 의사결정용)
        df["추천 강의반"] = df.get("ai_level", "").apply(classify_main_class)
        df["매물 트랙"] = df.get("main_property", "").apply(classify_property_track)
        preferred = [
            "id", "submitted_at", "business_name", "user_name", "email",
            "ai_level", "추천 강의반", "main_property", "매물 트랙",
            "custom_property", "ai_goals", "custom_goals",
        ]
        cols = [c for c in preferred if c in df.columns] + \
               [c for c in df.columns if c not in preferred]
        df = df[cols]
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 전체 응답 CSV 다운로드 (필터·분류 반영)",
            data=csv,
            file_name=f"shinhwa_responses_{datetime.now():%Y%m%d_%H%M}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary",
        )

    st.markdown(
        '<div class="footer">관리자 모드 · © 신화AI부동산</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────
# 0단계 — 면책조항 (일반 사용자)
# ─────────────────────────────────────────────
if not st.session_state.get("consented"):
    hero(
        title="신화AI부동산",
        subtitle="공인중개사 한 분 한 분에게 꼭 맞는 AI 학습 로드맵을 1분 안에 진단해드립니다.",
        pill="공인중개사 전용 진단",
    )

    st.markdown(
        """
        <div class="card">
          <h3>📌 이 진단의 목적</h3>
          <ul>
            <li><b>맞춤 진단</b> · 주력 매물 / 관심 업무 / AI 숙련도 3축으로 개인화된 로드맵을 산출합니다.</li>
            <li><b>실행 가능한 결과</b> · 추천 AI 도구 + 4주 학습 트랙이 함께 제공됩니다.</li>
            <li><b>PDF 보고서</b> · 결과를 1클릭으로 PDF 저장 — 내부 교육·고객 컨설팅 자료로 활용 가능합니다.</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card accent">
          <h3>🧭 활용 방법 (5단계)</h3>
          <ol style="padding-left:20px; margin:8px 0 0 0;">
            <li><b>사업자 상호 + 본인 성함 + 이메일</b> 입력</li>
            <li><b>주력 매물</b>(복수 선택 + 기타 직접 입력) 선택</li>
            <li><b>AI로 자동화·개선하고 싶은 업무</b>(복수 선택 + 기타 직접 입력) 선택</li>
            <li><b>현재 AI 활용 숙련도</b>를 5단계 중 선택</li>
            <li><b>‘진단받기’</b> 클릭 → 화면에 로드맵 + PDF 다운로드</li>
          </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card warning">
          <h3>⚖️ 면책 조항 (반드시 읽어주세요)</h3>
          <ul>
            <li>본 결과물은 <b>일반적인 정보 제공 및 교육 목적</b>의 참고자료이며,
                <b>법률·세무·금융·투자 자문이 아닙니다.</b></li>
            <li>본 결과물을 활용해 발생한 <b>모든 의사결정과 그 결과</b>는
                <b>전적으로 사용자 본인의 책임</b>이며, 신화AI부동산은
                <b>어떠한 책임도 지지 않습니다.</b></li>
            <li>추천 도구의 <b>이용 약관·요금·개인정보 처리 방침</b>은 사용자 본인이 직접 확인해주세요.</li>
            <li>입력하신 정보(사업자 상호·성함·이메일·응답)는 <b>신화AI부동산 강의/컨설팅 관리 및 통계</b> 목적으로
                저장됩니다. 본인의 응답은 다른 수강생에게 노출되지 않습니다.
                <b>민감 정보(주민번호·계좌·비밀번호 등)는 절대 입력하지 마세요.</b></li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    agreed = st.checkbox(
        "위 **이용 안내 및 면책 조항**을 모두 읽고 이해했으며, 이에 **동의**합니다.",
        value=st.session_state.get("agree_checkbox", False),
        key="agree_checkbox",
    )
    start = st.button("✅ 동의하고 진단 시작하기", type="primary", use_container_width=True)
    if start:
        if agreed:
            st.session_state.consented = True
            st.rerun()
        else:
            st.error("⚠️ 진단을 시작하려면 먼저 위의 **동의 체크박스**를 선택해주세요.")

    st.markdown(
        '<div class="footer">© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────
# 1단계 — 진단 설문
# ─────────────────────────────────────────────
hero(
    title="신화AI부동산 진단",
    subtitle="아래 항목을 입력해주시면 맞춤 AI 학습 로드맵이 즉시 생성됩니다.",
    pill="1분 진단",
)

with st.form("survey_form"):
    section_head("👤", "기본 정보")
    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input(
            "사업자 상호 *",
            placeholder="예) 신화공인중개사사무소",
            max_chars=60,
        )
    with col2:
        user_name = st.text_input(
            "본인 성함 *",
            placeholder="예) 홍길동",
            max_chars=30,
        )
    email = st.text_input(
        "이메일 주소 *",
        placeholder="예) you@example.com",
        max_chars=80,
        help="진단 결과 안내·후속 자료 발송에 사용됩니다. 본인 이외에 공개되지 않습니다.",
    )

    section_head("Q1", "주력으로 다루시는 매물·업무 종류")
    st.caption("해당되는 항목을 **복수 선택**해주세요.")
    main_property = st.multiselect(
        label="주력 매물",
        options=PROPERTY_OPTIONS,
        default=[],
        label_visibility="collapsed",
        placeholder="해당 매물을 선택하세요 (복수)",
    )
    custom_property = st.text_input(
        "기타 (분양·입주장·임대관리 등 직접 입력)",
        placeholder="예) 신축 단지 분양 + 입주장 컨설팅",
        key="custom_property_input",
    )

    section_head("Q2", "AI로 자동화·개선하고 싶은 업무")
    st.caption("**복수 선택** 가능합니다.")
    ai_goals = st.multiselect(
        label="AI 활용 목표",
        options=GOAL_OPTIONS,
        default=[],
        label_visibility="collapsed",
        placeholder="원하시는 업무를 선택하세요 (복수)",
    )
    custom_goals = st.text_area(
        "기타 (본인 상황에 맞는 업무를 직접 입력)",
        placeholder="예) 입주민 단톡방 자동 응대, 신축 모델하우스 동선 분석 등",
        height=90,
        key="custom_goals_input",
    )

    section_head("Q3", "현재 AI 활용 숙련도")
    ai_level = st.radio(
        label="숙련도",
        options=LEVEL_OPTIONS,
        index=1,
        label_visibility="collapsed",
    )

    st.markdown("&nbsp;")
    submitted = st.form_submit_button(
        "🎯 내 맞춤 AI 학습 로드맵 받기",
        use_container_width=True,
        type="primary",
    )

if submitted:
    errors: list[str] = []
    if not business_name.strip():
        errors.append("사업자 상호를 입력해주세요.")
    if not user_name.strip():
        errors.append("본인 성함을 입력해주세요.")
    if not email.strip():
        errors.append("이메일 주소를 입력해주세요.")
    elif not EMAIL_RE.match(email.strip()):
        errors.append("이메일 형식이 올바르지 않습니다. (예: you@example.com)")
    if not main_property and not custom_property.strip():
        errors.append("Q1의 주력 매물을 한 가지 이상 선택하거나 기타에 직접 입력해주세요.")
    if not ai_goals and not custom_goals.strip():
        errors.append("Q2의 AI 활용 목표를 한 가지 이상 선택하거나 기타에 직접 입력해주세요.")

    if errors:
        for msg in errors:
            st.warning(f"⚠️ {msg}")
    else:
        # 재진단 비교 — save_response 직전에 같은 이메일 이전 응답 받아둠
        # (이후 all_responses 호출은 새 응답까지 포함되므로 사전 캐싱이 안전)
        previous_responses = find_previous_responses(email.strip(), all_responses())

        new_id = save_response(
            business_name=business_name.strip(),
            user_name=user_name.strip(),
            email=email.strip(),
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
            ai_level=ai_level,
        )
        st.success(f"✅ 진단 완료! (응답 ID #{new_id})")

        # 강사 알림 메일 (설정 안 됐거나 실패해도 사용자 흐름엔 영향 없음)
        try:
            send_admin_notification({
                "id": new_id,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "business_name": business_name.strip(),
                "user_name": user_name.strip(),
                "email": email.strip(),
                "main_property": main_property,
                "custom_property": custom_property.strip(),
                "ai_goals": ai_goals,
                "custom_goals": custom_goals.strip(),
                "ai_level": ai_level,
            })
        except Exception:
            pass

        roadmap_md = generate_roadmap(
            business_name=business_name.strip(),
            user_name=user_name.strip(),
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
            ai_level=ai_level,
        )

        # 재진단 비교 카드 — 같은 이메일 이전 응답이 있으면 자동 표시 (없으면 숨김)
        if previous_responses:
            current_payload = {
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ai_level": ai_level,
                "main_property": main_property,
                "ai_goals": ai_goals,
            }
            comparison_data = build_comparison(current_payload, previous_responses[0])
            render_comparison_card(comparison_data, total_visits=len(previous_responses) + 1)

        # 진단 요약 — 칩 배지로 한눈에
        render_selection_chips(
            business_name=business_name.strip(),
            user_name=user_name.strip(),
            ai_level=ai_level,
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
        )

        with st.container(border=True):
            st.markdown(roadmap_md)

        with st.spinner("PDF 보고서를 만들고 있습니다..."):
            pdf_bytes = build_pdf(roadmap_md)

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe_biz = "".join(c for c in business_name if c.isalnum() or "가" <= c <= "힣")[:20]
        filename = f"신화AI부동산_AI로드맵_{safe_biz}_{ts}.pdf"
        st.download_button(
            label="📄 PDF 보고서로 저장하기",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
        st.caption(
            "이 PDF는 신화AI부동산이 발행한 공인중개사 전용 AI 학습 가이드입니다. "
            "면책 조항은 첫 화면 안내와 동일하게 적용됩니다."
        )

        # 수강생 본인 이메일로 PDF 자동 발송
        student_payload = {
            "id": new_id,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "business_name": business_name.strip(),
            "user_name": user_name.strip(),
            "email": email.strip(),
            "main_property": main_property,
            "custom_property": custom_property.strip(),
            "ai_goals": ai_goals,
            "custom_goals": custom_goals.strip(),
            "ai_level": ai_level,
        }
        if is_notify_active():
            with st.spinner(f"📧 {email.strip()} 주소로 결과 PDF를 보내드리고 있습니다..."):
                sent = send_student_pdf(student_payload, pdf_bytes, filename)
            if sent:
                st.success(
                    f"📬 입력하신 이메일 **{email.strip()}** 로 진단 결과 PDF를 발송했습니다.\n\n"
                    f"메일이 안 보이시면 **스팸함**을 한 번 확인해주세요."
                )
            else:
                st.info(
                    "ℹ️ 이메일 발송이 일시적으로 지연되고 있습니다. "
                    "위의 **'PDF 보고서로 저장하기'** 버튼으로 직접 받아두시면 됩니다."
                )

        # 카카오톡 공유 버튼 — 동료 중개사 추천 (앱 홍보)
        kakao_share_button()

        # 1:1 컨설팅 신청 CTA — Gmail 웹 + mailto + 복사 폴백 3종
        subj, body_text = _build_consult_message(
            business_name=business_name.strip(),
            user_name=user_name.strip(),
            email=email.strip(),
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
            ai_level=ai_level,
        )
        gmail_url = _build_gmail_url(subj, body_text)
        consulting_cta(gmail_url, subj, body_text)

st.markdown(
    '<div class="footer">© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구</div>',
    unsafe_allow_html=True,
)
