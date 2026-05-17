"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성기 (v2)
- 면책조항 동의 → 설문 → 로드맵 → PDF 다운로드
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
# 사이드바 (운영 대시보드)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 신화AI부동산 운영 현황")
    st.metric(label="누적 응답 수", value=f"{count_responses():,} 건")

    with st.expander("최근 응답 5건 보기"):
        recent = latest_responses(limit=5)
        if not recent:
            st.caption("_(아직 응답이 없습니다)_")
        for r in recent:
            st.markdown(
                f"**#{r['id']}** · {r['submitted_at']}  \n"
                f"{r['business_name']} / {r['user_name']}  \n"
                f"숙련도: {r['ai_level']}"
            )
            st.divider()

    if st.session_state.get("consented"):
        if st.button("🔄 처음부터 다시"):
            for k in ("consented", "submitted_payload"):
                st.session_state.pop(k, None)
            st.rerun()

# ─────────────────────────────────────────────
# 0단계 — 면책조항 & 안내 (동의 게이트)
# ─────────────────────────────────────────────
if not st.session_state.get("consented"):
    st.markdown(
        """
        <div style="text-align:center; padding:1.2rem 0;">
            <h1 style="margin-bottom:0.2rem;">🏠 신화AI부동산</h1>
            <h3 style="margin-top:0; color:#555; font-weight:400;">
                공인중개사 맞춤형 AI 학습 로드맵 진단
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📌 이 진단의 목적")
    st.markdown(
        "- **공인중개사 한 분 한 분에게 꼭 맞는 AI 학습 방향**을 1분 안에 제안해드립니다.\n"
        "- 주력 매물·업무 관심사·현재 AI 숙련도를 입력하시면, **추천 도구 + 4주 학습 트랙**이 자동 생성됩니다.\n"
        "- 결과는 **PDF 보고서로 다운로드**해 내부 교육·고객 컨설팅 자료로 활용하실 수 있습니다."
    )

    st.markdown("### 🧭 활용 방법")
    st.markdown(
        "1. **사업자 상호 + 본인 성함**을 입력합니다.\n"
        "2. **주력 매물(복수 선택 + 기타 자유 입력)**을 골라주세요.\n"
        "3. **AI로 자동화·개선하고 싶은 업무(복수 선택 + 기타 자유 입력)**를 골라주세요.\n"
        "4. **현재 AI 활용 숙련도**를 5단계 중에 선택합니다.\n"
        "5. ‘진단받기’를 누르면 **맞춤 로드맵**이 화면에 표시되고 **PDF 다운로드**도 가능합니다."
    )

    with st.container(border=True):
        st.markdown("### ⚖️ 면책 조항 (반드시 읽어주세요)")
        st.markdown(
            "- 본 웹앱이 제공하는 **AI 학습 로드맵·도구 추천·텍스트 결과물**은 "
            "**일반적인 정보 제공 및 교육 목적**의 참고자료입니다.\n"
            "- 본 결과물은 **법률·세무·금융·투자 자문이 아니며**, 특정 매물·계약·거래에 대한 "
            "**개별 조언으로 사용될 수 없습니다.**\n"
            "- 본 결과물을 활용해 발생한 **모든 의사결정과 그 결과**(영업, 광고, 계약, 투자, 데이터 입력 등)는 "
            "**전적으로 사용자 본인의 책임**이며, "
            "신화AI부동산은 이로 인한 **직접·간접 손해에 대해 어떠한 책임도 지지 않습니다.**\n"
            "- AI 도구 추천 목록은 **시장 상황 및 서비스 정책에 따라 변경**될 수 있으며, "
            "각 도구의 **이용 약관·요금·개인정보 처리 방침**은 사용자 본인이 직접 확인하셔야 합니다.\n"
            "- 입력하신 사업자 상호·성함·응답 내용은 **신화AI부동산이 서비스 개선 및 통계 분석 목적**으로 "
            "저장될 수 있습니다. 민감 정보(주민번호, 계좌, 비밀번호 등)는 절대 입력하지 마세요."
        )

    agreed = st.checkbox(
        "위 **이용 안내·면책 조항**을 모두 읽고 이해했으며, 이에 동의합니다.",
        key="agree_checkbox",
    )
    if st.button(
        "✅ 동의하고 진단 시작하기",
        disabled=not agreed,
        type="primary",
        use_container_width=True,
    ):
        st.session_state.consented = True
        st.rerun()

    st.divider()
    st.caption("© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구")
    st.stop()

# ─────────────────────────────────────────────
# 1단계 — 진단 설문
# ─────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding:1rem 0;">
        <h2 style="margin-bottom:0.2rem;">🏠 신화AI부동산 진단</h2>
        <p style="margin-top:0; color:#666;">아래 항목을 입력해주시면 맞춤 로드맵이 생성됩니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("survey_form"):
    # ── 사용자 정보 ─────────────────────────────
    st.subheader("👤 기본 정보")
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

    st.divider()

    # ── Q1. 주력 매물 (복수 + 기타) ────────────
    st.subheader("Q1. 주력으로 다루시는 매물·업무 종류는 무엇인가요?")
    st.caption("해당되는 항목을 **복수 선택**해주세요.")
    main_property = st.multiselect(
        label="주력 매물",
        options=PROPERTY_OPTIONS,
        default=[],
        label_visibility="collapsed",
    )
    custom_property = st.text_input(
        "기타 (분양·입주장·임대관리 등 직접 입력)",
        placeholder="예) 신축 단지 분양 + 입주장 컨설팅",
        key="custom_property_input",
    )

    st.divider()

    # ── Q2. AI 활용 목표 (복수 + 기타) ─────────
    st.subheader("Q2. AI로 가장 자동화/개선하고 싶은 업무는 무엇인가요?")
    st.caption("**복수 선택** 가능합니다.")
    ai_goals = st.multiselect(
        label="AI 활용 목표",
        options=GOAL_OPTIONS,
        default=[],
        label_visibility="collapsed",
    )
    custom_goals = st.text_area(
        "기타 (본인 상황에 맞는 업무를 직접 입력)",
        placeholder="예) 입주민 단톡방 자동 응대, 신축 모델하우스 동선 분석 등",
        height=80,
        key="custom_goals_input",
    )

    st.divider()

    # ── Q3. 숙련도 (5단계) ────────────────────
    st.subheader("Q3. 현재 AI 활용 숙련도는 어느 정도이신가요?")
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

        st.divider()
        st.markdown(roadmap_md)

        st.divider()
        with st.spinner("PDF 보고서를 만들고 있습니다..."):
            pdf_bytes = build_pdf(roadmap_md)

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe_biz = "".join(c for c in business_name if c.isalnum() or c in "가-힣")[:20]
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
            "면책 조항은 첫 화면에서 안내드린 내용과 동일하게 적용됩니다."
        )

st.divider()
st.caption("© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구")
