"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성기
설문 UI 프로토타입 (feat-ui)
"""
import streamlit as st
from db import init_db, save_response, count_responses, latest_responses

# 앱 기동 시 DB 초기화 (테이블 없으면 생성)
init_db()

st.set_page_config(
    page_title="신화AI부동산 | AI 학습 로드맵 진단",
    page_icon="🏠",
    layout="centered",
)

# ─────────────────────────────────────────────
# 사이드바 — 운영 대시보드 (신화AI부동산 내부용)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 신화AI부동산 운영 현황")
    total = count_responses()
    st.metric(label="누적 응답 수", value=f"{total:,} 건")

    with st.expander("최근 응답 5건 보기"):
        for r in latest_responses(limit=5):
            st.markdown(
                f"**#{r['id']}** · {r['submitted_at']}  \n"
                f"매물: {r['main_property']} / 숙련도: {r['ai_level']}  \n"
                f"목표: {', '.join(r['ai_goals']) if r['ai_goals'] else '_(없음)_'}"
            )
            st.divider()

# ─────────────────────────────────────────────
# 헤더 (브랜딩)
# ─────────────────────────────────────────────
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

st.info(
    "안녕하세요, 공인중개사님 👋\n\n"
    "아래 3가지 질문에 답해주시면, **현재 업무와 숙련도에 꼭 맞는** "
    "AI 학습 로드맵을 즉시 제안해드립니다. (소요 시간 약 1분)"
)

st.divider()

# ─────────────────────────────────────────────
# 설문 폼
# ─────────────────────────────────────────────
with st.form("survey_form"):
    st.subheader("Q1. 주력으로 다루시는 매물 종류는 무엇인가요?")
    main_property = st.radio(
        label="하나만 선택해주세요",
        options=["아파트", "상가", "토지", "빌라·다세대"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.subheader("Q2. AI로 가장 자동화/개선하고 싶은 업무는 무엇인가요?")
    st.caption("복수 선택이 가능합니다.")
    ai_goals = st.multiselect(
        label="AI 활용 목표",
        options=[
            "블로그·SNS 콘텐츠 자동 작성",
            "매물 시세·입지 분석",
            "고객 상담·문의 응대",
            "광고 카피·문구 제작",
        ],
        default=[],
        label_visibility="collapsed",
    )

    st.subheader("Q3. 현재 AI 활용 숙련도는 어느 정도이신가요?")
    ai_level = st.select_slider(
        label="숙련도",
        options=["하 (입문)", "중 (기본 사용 가능)", "상 (능숙)"],
        value="중 (기본 사용 가능)",
        label_visibility="collapsed",
    )

    st.markdown("&nbsp;")
    submitted = st.form_submit_button(
        "🎯 내 맞춤 AI 학습 로드맵 받기",
        use_container_width=True,
        type="primary",
    )

# ─────────────────────────────────────────────
# 제출 결과 (다음 단계에서 로직 연결)
# ─────────────────────────────────────────────
if submitted:
    if not ai_goals:
        st.warning("⚠️ Q2의 AI 활용 목표를 한 가지 이상 선택해주세요.")
    else:
        new_id = save_response(main_property, ai_goals, ai_level)
        st.success(
            f"✅ 설문이 제출되었습니다. (응답 ID #{new_id} · 누적 {count_responses()}건)"
        )
        with st.expander("📋 제출된 답변 확인", expanded=True):
            st.write(f"- **주력 매물**: {main_property}")
            st.write(f"- **AI 활용 목표**: {', '.join(ai_goals)}")
            st.write(f"- **AI 숙련도**: {ai_level}")
        st.info("💡 로드맵 생성·PDF 다운로드는 6단계에서 통합됩니다.")

# ─────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────
st.divider()
st.caption("© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구")
