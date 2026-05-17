"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성기 (v2.1)
- 면책조항 동의 → 설문 → 로드맵 → PDF 다운로드
- 카드 기반 디자인, 색상 액센트, 아이콘 섹션
"""
import streamlit as st
from datetime import datetime

from db import init_db, save_response, count_responses, latest_responses
from roadmap_logic import (
    generate_roadmap,
    PROPERTY_OPTIONS,
    GOAL_OPTIONS,
    LEVEL_OPTIONS,
)
from pdf_export import build_pdf

init_db()

st.set_page_config(
    page_title="신화AI부동산 | AI 학습 로드맵 진단",
    page_icon="🏠",
    layout="centered",
)

# ─────────────────────────────────────────────
# 글로벌 스타일 (디자인 토큰)
# ─────────────────────────────────────────────
PRIMARY = "#0F3D77"   # 신화 네이비
ACCENT = "#FFB400"    # 포인트 옐로
BG_SOFT = "#F4F7FB"   # 카드 배경

st.markdown(
    f"""
    <style>
      /* 기본 폰트 & 배경 */
      .stApp {{
        background: linear-gradient(180deg, #FAFBFD 0%, #F4F7FB 100%);
      }}

      /* 히어로 영역 */
      .hero {{
        background: linear-gradient(135deg, {PRIMARY} 0%, #1B5BB0 100%);
        color: white;
        border-radius: 16px;
        padding: 28px 24px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(15,61,119,0.18);
      }}
      .hero h1 {{
        color: white !important;
        margin: 0 0 6px 0 !important;
        font-size: 1.9rem !important;
      }}
      .hero p {{
        color: rgba(255,255,255,0.92);
        margin: 0;
        font-size: 1rem;
      }}
      .hero .pill {{
        display: inline-block;
        background: {ACCENT};
        color: {PRIMARY};
        padding: 4px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.78rem;
        margin-bottom: 10px;
        letter-spacing: 0.3px;
      }}

      /* 카드 (info / step / disclaimer) */
      .card {{
        background: white;
        border-radius: 14px;
        padding: 20px 22px;
        margin: 12px 0;
        box-shadow: 0 2px 10px rgba(15,61,119,0.06);
        border-left: 6px solid {PRIMARY};
      }}
      .card.warning {{ border-left-color: #E04A4A; }}
      .card.accent  {{ border-left-color: {ACCENT}; }}
      .card h3 {{
        margin-top: 0 !important;
        color: {PRIMARY};
        font-size: 1.15rem;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .card ul {{ margin: 8px 0 0 0; padding-left: 20px; }}
      .card li {{ margin: 6px 0; line-height: 1.55; }}

      /* 섹션 헤더 (설문 폼 내부) */
      .section-head {{
        display: flex;
        align-items: center;
        gap: 10px;
        background: {BG_SOFT};
        padding: 10px 14px;
        border-radius: 10px;
        margin: 18px 0 10px 0;
        border-left: 4px solid {PRIMARY};
      }}
      .section-head .badge {{
        background: {PRIMARY};
        color: white;
        width: 26px; height: 26px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
      }}
      .section-head .label {{
        font-weight: 700;
        color: {PRIMARY};
        font-size: 1.02rem;
      }}

      /* 일반 버튼 강조 */
      .stButton > button[kind="primary"],
      .stDownloadButton > button[kind="primary"],
      .stFormSubmitButton > button[kind="primary"] {{
        background: {PRIMARY} !important;
        border: none !important;
        height: 48px;
        font-weight: 700;
        letter-spacing: 0.2px;
      }}
      .stButton > button[kind="primary"]:hover,
      .stDownloadButton > button[kind="primary"]:hover,
      .stFormSubmitButton > button[kind="primary"]:hover {{
        background: #0a2c5a !important;
      }}

      /* 푸터 */
      .footer {{
        text-align: center;
        color: #8A95A6;
        font-size: 0.82rem;
        margin-top: 20px;
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
# 사이드바 (운영 대시보드)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h3 style='color:{PRIMARY};margin-top:0;'>📊 신화AI부동산</h3>", unsafe_allow_html=True)
    st.caption("운영 대시보드")
    st.metric(label="누적 응답 수", value=f"{count_responses():,} 건")

    with st.expander("최근 응답 5건 보기"):
        recent = latest_responses(limit=5)
        if not recent:
            st.caption("_(아직 응답이 없습니다)_")
        for r in recent:
            st.markdown(
                f"**#{r['id']}** · {r['submitted_at']}  \n"
                f"{r['business_name'] or '_(상호 없음)_'} / {r['user_name'] or '_(성함 없음)_'}  \n"
                f"숙련도: {r['ai_level'] or '_(미입력)_'}"
            )
            st.divider()

    if st.session_state.get("consented"):
        if st.button("🔄 처음부터 다시", use_container_width=True):
            for k in ("consented", "submitted_payload"):
                st.session_state.pop(k, None)
            st.rerun()

# ─────────────────────────────────────────────
# 0단계 — 면책조항 & 안내 (동의 게이트)
# ─────────────────────────────────────────────
if not st.session_state.get("consented"):
    hero(
        title="신화AI부동산",
        subtitle="공인중개사 한 분 한 분에게 꼭 맞는 AI 학습 로드맵을 1분 안에 진단해드립니다.",
        pill="공인중개사 전용 진단",
    )

    # 목적 카드
    st.markdown(
        f"""
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

    # 활용 방법 카드
    st.markdown(
        f"""
        <div class="card accent">
          <h3>🧭 활용 방법 (5단계)</h3>
          <ol style="padding-left:20px; margin:8px 0 0 0;">
            <li><b>사업자 상호 + 본인 성함</b> 입력</li>
            <li><b>주력 매물</b>(복수 선택 + 기타 직접 입력) 선택</li>
            <li><b>AI로 자동화·개선하고 싶은 업무</b>(복수 선택 + 기타 직접 입력) 선택</li>
            <li><b>현재 AI 활용 숙련도</b>를 5단계 중 선택</li>
            <li><b>‘진단받기’</b> 클릭 → 화면에 로드맵 + PDF 다운로드</li>
          </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 면책조항 카드
    st.markdown(
        """
        <div class="card warning">
          <h3>⚖️ 면책 조항 (반드시 읽어주세요)</h3>
          <ul>
            <li>본 결과물은 <b>일반적인 정보 제공 및 교육 목적</b>의 참고자료이며,
                <b>법률·세무·금융·투자 자문이 아닙니다.</b></li>
            <li>본 결과물을 활용해 발생한 <b>모든 의사결정과 그 결과</b>(영업·광고·계약·투자 등)는
                <b>전적으로 사용자 본인의 책임</b>이며, 신화AI부동산은
                <b>이로 인한 직접·간접 손해에 대해 어떠한 책임도 지지 않습니다.</b></li>
            <li>추천 도구의 <b>이용 약관·요금·개인정보 처리 방침</b>은 사용자 본인이 직접 확인해주세요.</li>
            <li>입력하신 사업자 상호·성함·응답은 <b>서비스 개선·통계 분석</b> 목적으로 저장될 수 있습니다.
                <b>민감 정보(주민번호·계좌·비밀번호 등)는 절대 입력하지 마세요.</b></li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 동의 영역 — 체크박스 + 항상 활성화된 버튼 (클릭 시 동의 확인)
    agreed = st.checkbox(
        "위 **이용 안내 및 면책 조항**을 모두 읽고 이해했으며, 이에 **동의**합니다.",
        value=st.session_state.get("agree_checkbox", False),
        key="agree_checkbox",
    )
    start = st.button(
        "✅ 동의하고 진단 시작하기",
        type="primary",
        use_container_width=True,
        key="start_button",
    )
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
    # ── 기본 정보 ─────────────────────────────
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

    # ── Q1. 주력 매물 ─────────────────────────
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

    # ── Q2. AI 활용 목표 ──────────────────────
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

    # ── Q3. 숙련도 ────────────────────────────
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

# ─────────────────────────────────────────────
# 제출 처리 — 검증 + 로드맵 + PDF
# ─────────────────────────────────────────────
if submitted:
    errors: list[str] = []
    if not business_name.strip():
        errors.append("사업자 상호를 입력해주세요.")
    if not user_name.strip():
        errors.append("본인 성함을 입력해주세요.")
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
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
            ai_level=ai_level,
        )
        st.success(f"✅ 진단 완료! (응답 ID #{new_id} · 누적 {count_responses()}건)")

        roadmap_md = generate_roadmap(
            business_name=business_name.strip(),
            user_name=user_name.strip(),
            main_property=main_property,
            custom_property=custom_property.strip(),
            ai_goals=ai_goals,
            custom_goals=custom_goals.strip(),
            ai_level=ai_level,
        )

        # 로드맵을 카드 컨테이너로 감싸기
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

st.markdown(
    '<div class="footer">© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구</div>',
    unsafe_allow_html=True,
)
