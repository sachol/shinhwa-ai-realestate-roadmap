"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성기 (v3)
- 면책 동의 → 설문(이메일 필수) → 로드맵 → PDF
- 공개 사이드바: 누적 응답 수만 노출 (개인정보 미노출)
- 관리자 모드: 사이드바 비밀번호 입력 시 전체 응답(상호/성함/이메일) 조회
- 저장소: Google Sheets 우선, 미설정 시 SQLite 폴백
"""
import re
import pandas as pd
import streamlit as st
from datetime import datetime

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
        --sh-hero-shadow:0 10px 30px rgba(15,61,119,0.18);
        --sh-warning:    #E04A4A;
      }}
      @media (prefers-color-scheme: dark) {{
        :root {{
          --sh-card-bg:    #1E2733;
          --sh-card-text:  #E8EEF7;
          --sh-section-bg: #1A2230;
          --sh-section-fg: #BFD3F0;
          --sh-muted:      #8E9BB0;
          --sh-shadow:     0 2px 10px rgba(0,0,0,0.35);
          --sh-hero-shadow:0 10px 30px rgba(0,0,0,0.45);
          --sh-warning:    #FF7575;
        }}
      }}
      .hero {{
        background: linear-gradient(135deg, var(--sh-primary) 0%, var(--sh-primary-2) 100%);
        color: #FFFFFF;
        border-radius: 16px;
        padding: 28px 24px;
        margin-bottom: 18px;
        box-shadow: var(--sh-hero-shadow);
      }}
      .hero h1 {{ color: #FFF !important; margin: 0 0 6px 0 !important; font-size: 1.9rem !important; }}
      .hero p  {{ color: rgba(255,255,255,0.92); margin: 0; font-size: 1rem; }}
      .hero .pill {{
        display:inline-block; background: var(--sh-accent); color:#0F3D77;
        padding: 4px 12px; border-radius: 999px; font-weight:700; font-size:0.78rem;
        margin-bottom: 10px; letter-spacing: 0.3px;
      }}
      .card {{
        background: var(--sh-card-bg); color: var(--sh-card-text);
        border-radius: 14px; padding: 20px 22px; margin: 12px 0;
        box-shadow: var(--sh-shadow); border-left: 6px solid var(--sh-primary);
      }}
      .card.warning {{ border-left-color: var(--sh-warning); }}
      .card.accent  {{ border-left-color: var(--sh-accent); }}
      .card h3 {{ margin-top:0 !important; color: var(--sh-section-fg);
                 font-size: 1.15rem; display:flex; align-items:center; gap:8px; }}
      .card ul, .card ol {{ margin: 8px 0 0 0; padding-left:20px; }}
      .card li {{ margin: 6px 0; line-height: 1.55; color: var(--sh-card-text); }}
      .card b  {{ color: var(--sh-card-text); }}
      .section-head {{
        display:flex; align-items:center; gap:10px;
        background: var(--sh-section-bg); padding: 10px 14px; border-radius: 10px;
        margin: 18px 0 10px 0; border-left: 4px solid var(--sh-primary);
      }}
      .section-head .badge {{
        background: var(--sh-primary); color:#FFF; width:26px; height:26px;
        border-radius: 50%; display:inline-flex; align-items:center; justify-content:center;
        font-weight: 700; font-size: 0.85rem;
      }}
      .section-head .label {{ font-weight: 700; color: var(--sh-section-fg); font-size: 1.02rem; }}
      .stButton > button[kind="primary"],
      .stDownloadButton > button[kind="primary"],
      .stFormSubmitButton > button[kind="primary"] {{
        background: var(--sh-primary) !important; border:none !important;
        color:#FFF !important; height:48px; font-weight:700;
      }}
      .stButton > button[kind="primary"]:hover,
      .stDownloadButton > button[kind="primary"]:hover,
      .stFormSubmitButton > button[kind="primary"]:hover {{ background:#0a2c5a !important; }}
      .footer {{ text-align:center; color: var(--sh-muted); font-size:0.82rem; margin-top:20px; }}
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

st.markdown(
    '<div class="footer">© 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구</div>',
    unsafe_allow_html=True,
)
