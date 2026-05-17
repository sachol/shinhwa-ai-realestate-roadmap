"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성기 (v3)
- 면책 동의 → 설문(이메일 필수) → 로드맵 → PDF
- 공개 사이드바: 누적 응답 수만 노출 (개인정보 미노출)
- 관리자 모드: 사이드바 비밀번호 입력 시 전체 응답(상호/성함/이메일) 조회
- 저장소: Google Sheets 우선, 미설정 시 SQLite 폴백
"""
import re
import urllib.parse
import pandas as pd
import streamlit as st
from datetime import datetime

# 1:1 컨설팅 문의 수신 메일 (CTA mailto 대상)
CONSULT_EMAIL = "sachol.cap@gmail.com"

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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">
    <style>
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


def _build_consult_mailto(
    business_name: str,
    user_name: str,
    email: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> str:
    """수강생 정보·진단 요약이 미리 채워진 1:1 컨설팅 문의 mailto 링크 생성."""
    subject = f"[신화AI부동산] 1:1 컨설팅 문의 — {business_name} / {user_name}"
    body_lines = [
        f"안녕하세요, 신화 대표님.",
        f"",
        f"신화AI부동산 진단을 받아본 {business_name}의 {user_name}입니다.",
        f"진단 결과를 바탕으로, 1:1 맞춤 컨설팅을 받아보고 싶습니다.",
        f"",
        f"────────────────────────",
        f"■ 제 진단 요약",
        f"────────────────────────",
        f"· 사업자 상호: {business_name}",
        f"· 성함: {user_name}",
        f"· 이메일: {email}",
        f"· AI 숙련도: {ai_level}",
        f"· 주력 매물: {', '.join(main_property) if main_property else '(없음)'}",
    ]
    if custom_property:
        body_lines.append(f"· 기타 매물·업무: {custom_property}")
    body_lines.append(
        f"· AI 활용 목표: {', '.join(ai_goals) if ai_goals else '(없음)'}"
    )
    if custom_goals:
        body_lines.append(f"· 기타 업무 (직접 입력): {custom_goals}")
    body_lines += [
        f"",
        f"────────────────────────",
        f"■ 컨설팅에서 다루고 싶은 내용 (자유롭게 작성)",
        f"────────────────────────",
        f"(여기에 구체적으로 어떤 부분을 더 깊게 다루고 싶은지 적어주세요)",
        f"",
        f"",
        f"────────────────────────",
        f"■ 희망 일정 / 연락 가능 시간",
        f"────────────────────────",
        f"(편하신 시간대 알려주세요)",
        f"",
        f"감사합니다.",
        f"{user_name} 드림",
    ]
    body = "\n".join(body_lines)
    return (
        f"mailto:{CONSULT_EMAIL}"
        f"?subject={urllib.parse.quote(subject)}"
        f"&body={urllib.parse.quote(body)}"
    )


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


def consulting_cta(mailto_url: str) -> None:
    """결과 페이지 하단의 1:1 컨설팅 신청 CTA 카드."""
    st.markdown(
        f"""
        <div class="shinhwa-cta-card">
          <span class="pill">⭐ 수강생 전용 한정 혜택</span>
          <h3>더 깊은 1:1 맞춤 컨설팅이 필요하신가요?</h3>
          <p style="margin:0 0 16px 0; font-size:0.95rem; line-height:1.6;">
            진단 결과를 바탕으로 <b>주력 매물·고객층·업무 환경</b>에 꼭 맞는
            AI 자동화 설계를 받아보실 수 있습니다.<br>
            <b>수강생분께만</b> 신화AI부동산의 노하우와 시간을 우선 배정해드립니다.
          </p>
          <a href="{mailto_url}" class="shinhwa-cta-btn">
            <span class="btn-text">📧 신화 대표에게 컨설팅 문의하기</span>
          </a>
          <p class="cta-hint">
            💡 버튼을 누르시면 메일 앱이 열리며,
            <b style="color:#3A4250 !important;">진단 요약이 자동으로 본문에 채워집니다.</b>
            희망 일정과 다루고 싶은 주제만 추가로 적어 보내주세요.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
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
        subtitle="모든 응답을 조회하고 CSV로 다운로드할 수 있습니다.",
        pill="ADMIN",
    )

    rows = all_responses()
    st.markdown(f"### 📋 전체 응답 ({len(rows)}건)")
    if not rows:
        st.info("아직 응답이 없습니다.")
    else:
        df = pd.DataFrame(rows)
        # 보기 좋게 컬럼 순서 정렬
        preferred = [
            "id", "submitted_at", "business_name", "user_name", "email",
            "ai_level", "main_property", "custom_property",
            "ai_goals", "custom_goals",
        ]
        cols = [c for c in preferred if c in df.columns] + \
               [c for c in df.columns if c not in preferred]
        df = df[cols]
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 전체 응답 CSV 다운로드",
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

        # 1:1 컨설팅 신청 CTA
        consulting_cta(_build_consult_mailto(
            business_name=business_name.strip(),
            user_name=user_name.strip(),
            email=email.strip(),
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
            ai_level=ai_level,
        ))

st.markdown(
    '<div class="footer">© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구</div>',
    unsafe_allow_html=True,
)
