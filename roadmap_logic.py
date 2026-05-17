"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성 로직 (v2)
- 주력 매물: 복수 선택 + 기타 자유 입력
- AI 활용 목표: 12종 + 기타 자유 입력
- 숙련도: 5단계 세분화
- 사업자 상호 + 본인 성함 반영
- 발행 일시(날짜+시간) 자동 삽입
"""
from __future__ import annotations
from datetime import datetime

PROPERTY_OPTIONS = [
    "아파트",
    "상가",
    "토지",
    "빌라·다세대",
    "오피스텔",
    "단독·다가구",
    "분양권",
    "재개발·재건축",
    "공장·창고",
    "농지·임야",
]

GOAL_OPTIONS = [
    "블로그·SNS 콘텐츠 자동 작성",
    "매물 시세·입지 분석",
    "고객 상담·문의 응대",
    "광고 카피·문구 제작",
    "매물 사진·영상 편집/생성",
    "계약서·서류 작성 보조",
    "시장 동향·뉴스 요약",
    "임장(현장 답사) 리포트 자동화",
    "고객 관리(CRM) 자동화",
    "음성→텍스트 회의록·상담 정리",
    "부동산 교육 콘텐츠 제작",
    "세무·법률 정보 빠른 검색",
]

LEVEL_OPTIONS = [
    "1. 입문 — AI를 거의 써본 적 없음",
    "2. 기초 — ChatGPT 등을 한두 번 써본 정도",
    "3. 기본 활용 — 업무에 가끔 사용",
    "4. 능숙 활용 — 업무에 일상적으로 사용",
    "5. 전문가 자동화 — 커스텀 GPT/매크로/자동화 구축 가능",
]

GOAL_TO_TOOLS: dict[str, list[dict]] = {
    "블로그·SNS 콘텐츠 자동 작성": [
        {"name": "ChatGPT / Claude", "why": "매물 소개 글·블로그 포스팅 초안을 1분 만에 생성"},
        {"name": "Notion AI", "why": "콘텐츠 일정·아이디어 보드를 자동 정리"},
        {"name": "Canva AI / Gamma", "why": "글 + 이미지·카드뉴스를 동시에 제작"},
    ],
    "매물 시세·입지 분석": [
        {"name": "국토교통부 실거래가 공공데이터 API", "why": "실거래 가격 추세를 자동 수집"},
        {"name": "Claude + Excel/CSV", "why": "수집한 데이터를 자연어 질문으로 분석"},
        {"name": "호갱노노 / 아실 / 부동산지인", "why": "단지·지역 정보를 빠르게 크로스체크"},
    ],
    "고객 상담·문의 응대": [
        {"name": "ChatGPT 커스텀 GPT", "why": "자주 묻는 질문(FAQ)을 학습시킨 24시간 상담봇"},
        {"name": "채널톡·카카오톡 챗봇 빌더", "why": "실 채널에 연결해 1차 응대 자동화"},
        {"name": "Claude Projects", "why": "고객별 상담 이력·메모를 한 공간에서 관리"},
    ],
    "광고 카피·문구 제작": [
        {"name": "ChatGPT / Claude", "why": "매물별 광고 카피 A/B안을 즉시 생성"},
        {"name": "뤼튼 (Wrtn)", "why": "한국어 광고 문구·블로그 카피에 특화"},
        {"name": "Midjourney / DALL·E", "why": "광고용 시각 컨셉 이미지 생성"},
    ],
    "매물 사진·영상 편집/생성": [
        {"name": "Canva / Photoroom", "why": "매물 사진 배경 제거·보정을 1초에"},
        {"name": "Runway / Pika", "why": "사진 한 장으로 매물 소개 영상 생성"},
        {"name": "CapCut + AI 자막", "why": "임장 영상에 자동 자막·BGM 삽입"},
    ],
    "계약서·서류 작성 보조": [
        {"name": "Claude Projects (계약서 분석)", "why": "PDF 계약서를 올리고 ‘위험 조항만 찾아줘’ 식 분석"},
        {"name": "ChatGPT + 표준 약관 템플릿", "why": "특약 조항 초안 자동 작성"},
        {"name": "DocuSign / 모두싸인", "why": "전자서명·발송 자동화"},
    ],
    "시장 동향·뉴스 요약": [
        {"name": "Perplexity / Google AI Overview", "why": "‘오늘 OO지역 부동산 뉴스 요약해줘’ 즉답"},
        {"name": "ChatGPT 데일리 브리핑", "why": "관심 키워드 자동 모니터링"},
        {"name": "Feedly + Claude", "why": "RSS 뉴스를 매일 자동 요약"},
    ],
    "임장(현장 답사) 리포트 자동화": [
        {"name": "스마트폰 음성녹음 + Whisper/Clova Note", "why": "임장 중 음성을 자동 텍스트화"},
        {"name": "ChatGPT 음성 모드", "why": "현장에서 바로 질문·메모 가능"},
        {"name": "Notion + AI", "why": "사진·메모·텍스트를 한 페이지 리포트로 자동 정리"},
    ],
    "고객 관리(CRM) 자동화": [
        {"name": "구글 스프레드시트 + ChatGPT 연동", "why": "고객 응대 로그를 자동 분류·태깅"},
        {"name": "Zapier / Make.com", "why": "카카오톡·문자·메일을 CRM에 자동 기록"},
        {"name": "Airtable + AI", "why": "고객별 매물 매칭 점수 자동 산정"},
    ],
    "음성→텍스트 회의록·상담 정리": [
        {"name": "Clova Note (네이버)", "why": "한국어 회의록 변환·요약 강력"},
        {"name": "Whisper / Tiro", "why": "장시간 녹음도 정확하게 텍스트화"},
        {"name": "ChatGPT 후처리", "why": "텍스트를 ‘액션 아이템’ 중심으로 재정리"},
    ],
    "부동산 교육 콘텐츠 제작": [
        {"name": "Gamma / Tome", "why": "주제만 입력하면 강의용 슬라이드 자동 생성"},
        {"name": "ChatGPT + 스크립트 작성", "why": "유튜브·블로그 강의 스크립트 초안 즉시 생성"},
        {"name": "HeyGen / D-ID", "why": "AI 아바타로 강의 영상 제작"},
    ],
    "세무·법률 정보 빠른 검색": [
        {"name": "Perplexity (출처 표기)", "why": "법령·세율 변경을 출처 링크와 함께 확인"},
        {"name": "Claude Projects (자료실)", "why": "자주 보는 법령 PDF를 올려두고 자연어 질문"},
        {"name": "국세청 홈택스 + AI 요약", "why": "복잡한 세무 안내문을 한 줄로 요약"},
    ],
}

PROPERTY_HOOKS: dict[str, str] = {
    "아파트": "동일 단지·평형 실거래 추이를 Claude에 붙여넣고 ‘지난 6개월 동향 요약’ 받기",
    "상가": "상권 유동인구·업종 분포 데이터를 AI에 분석시켜 ‘이 자리 적합 업종’ 인사이트 받기",
    "토지": "용도지역·지목·공시지가를 표로 정리해 AI에게 ‘투자 매력도 점수’ 요청",
    "빌라·다세대": "동일 권역 빌라 거래량·전세가율을 AI로 비교해 매도/매수 타이밍 리포트화",
    "오피스텔": "수익률(월세/매매가) 데이터를 AI로 동일 권역과 비교해 투자 메리트 점수화",
    "단독·다가구": "토지+건물 가치 분리 분석을 AI에게 시켜 재건축·리모델링 타당성 평가",
    "분양권": "전매 제한·중도금 일정·웃돈 추이를 표로 정리해 AI에게 협상 포인트 자문",
    "재개발·재건축": "조합·정비구역 단계별 일정과 분담금 시뮬레이션을 AI로 비교 분석",
    "공장·창고": "물류 동선·진입로·전력 인프라를 AI에게 점수화시켜 산업 입지 보고서 작성",
    "농지·임야": "용도 변경 가능성·도로 접근성·인근 개발 호재를 AI에게 정리시켜 투자 등급 산정",
}

LEVEL_TRACKS: dict[str, list[str]] = {
    "1. 입문 — AI를 거의 써본 적 없음": [
        "1주차: ChatGPT 또는 Claude 무료 계정 만들기 — 첫 질문 5개 던져보기",
        "2주차: 매물 소개 글 한 편을 AI와 같이 작성해보기 (지난 매물 1건 골라서)",
        "3주차: ‘역할·맥락·요구사항’ 3박자 프롬프트 작성법 익히기",
        "4주차: 자주 쓰는 업무 3개에 대한 ‘나만의 프롬프트 템플릿’ 1쪽 만들기",
    ],
    "2. 기초 — ChatGPT 등을 한두 번 써본 정도": [
        "1주차: 유료 플랜(ChatGPT Plus 또는 Claude Pro) 도입 검토 — 무료/유료 비교 체험",
        "2주차: 매물 소개·블로그·고객 문자 등 ‘반복 업무 3종’ AI 자동화",
        "3주차: 파일 업로드 활용 — 계약서/실거래 PDF를 AI에 올려 분석시키기",
        "4주차: 한 주간 절약한 시간(분 단위) 측정 + 동료에게 사례 1건 공유",
    ],
    "3. 기본 활용 — 업무에 가끔 사용": [
        "1주차: 커스텀 GPT / Claude Projects 만들기 — 신화AI부동산 전용 ‘업무 비서’ 1개 구축",
        "2주차: 실거래가 공공데이터 API + Claude/Excel 연동으로 자동 보고서 만들기",
        "3주차: 블로그·SNS 발행 워크플로 자동화 (Notion AI + Canva AI 조합)",
        "4주차: 고객 1차 응대 챗봇 프로토타입 구축(채널톡·카카오톡)",
    ],
    "4. 능숙 활용 — 업무에 일상적으로 사용": [
        "1주차: Zapier/Make.com으로 카카오톡·문자·CRM 사이 데이터 자동 흐름 구축",
        "2주차: 음성→텍스트(Clova/Whisper) 기반 임장 리포트·상담 자동화 파이프라인",
        "3주차: 매물 추천 점수 모델(엑셀+AI)로 고객 매칭 자동화",
        "4주차: 광고·콘텐츠 A/B 테스트를 AI에게 분석시키고 다음 캠페인 자동 제안",
    ],
    "5. 전문가 자동화 — 커스텀 GPT/매크로/자동화 구축 가능": [
        "1주차: Claude Code · MCP Server로 본인 DB/CRM에 직접 연결하는 자동화 구축",
        "2주차: Agent Teams 패턴으로 ‘리서처 + 카피라이터 + 디자이너’ AI 팀 구성",
        "3주차: Streamlit/Next.js로 사내·고객용 AI 진단/매칭 웹앱 직접 제작",
        "4주차: 신화AI부동산의 노하우를 동료 중개사·수강생에게 교육 콘텐츠로 자산화",
    ],
}


def _format_tools_section(ai_goals: list[str], custom_goals: str) -> str:
    if not ai_goals and not custom_goals.strip():
        return "_(AI 활용 목표가 선택되지 않았습니다.)_"
    lines: list[str] = []
    for goal in ai_goals:
        lines.append(f"\n### 🎯 목표: {goal}")
        tools = GOAL_TO_TOOLS.get(goal, [])
        if not tools:
            lines.append("- _(추천 도구가 매핑되어 있지 않습니다.)_")
        for t in tools:
            lines.append(f"- **{t['name']}** — {t['why']}")
    if custom_goals.strip():
        lines.append("\n### 🎯 목표 (직접 입력): " + custom_goals.strip())
        lines.append(
            "- 위 업무는 표준 매핑이 없으므로, 신화AI부동산에서 별도 1:1 자문을 권장드립니다."
        )
        lines.append(
            "- 일반 권장 출발 도구: **ChatGPT / Claude / Perplexity** 3종 중 한 가지로 "
            "‘문제 정의 → 시범 적용 → 측정’ 사이클부터 시작하세요."
        )
    return "\n".join(lines)


def _format_property_section(main_property: list[str], custom_property: str) -> str:
    if not main_property and not custom_property.strip():
        return "_(주력 매물이 선택되지 않았습니다.)_"
    lines: list[str] = []
    for p in main_property:
        hook = PROPERTY_HOOKS.get(p)
        if hook:
            lines.append(f"- **{p}** — {hook}")
        else:
            lines.append(f"- **{p}**")
    if custom_property.strip():
        lines.append(
            f"- **기타 (직접 입력)**: {custom_property.strip()} — 해당 업무에 대해서는 "
            "신화AI부동산이 추가 자문을 제공해드릴 수 있습니다."
        )
    return "\n".join(lines)


def _format_track(ai_level: str) -> str:
    track = LEVEL_TRACKS.get(ai_level, [])
    if not track:
        return "_(숙련도가 선택되지 않았습니다.)_"
    return "\n".join(f"- {item}" for item in track)


def generate_roadmap(
    *,
    business_name: str,
    user_name: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> str:
    now = datetime.now()
    issued_at = now.strftime("%Y년 %m월 %d일 %H:%M")

    biz = business_name.strip() or "(상호 미입력)"
    name = user_name.strip() or "공인중개사"

    return f"""# 🏠 신화AI부동산 맞춤 AI 학습 로드맵

> **발행일시**: {issued_at}
> **수신**: {biz} / {name} 공인중개사님
> **숙련도**: {ai_level}

---

## 1. 진단 요약

**{name}** 공인중개사님은 **{biz}**에서 활동하시며,
현재 AI 활용 수준은 **{ai_level}** 단계입니다.

### 주력 업무 영역
{_format_property_section(main_property, custom_property)}

---

## 2. 목표별 추천 AI 도구
{_format_tools_section(ai_goals, custom_goals)}

---

## 3. 4주 학습 트랙 (숙련도 **{ai_level}** 기준)

{_format_track(ai_level)}

---

## 4. 다음 액션 — 오늘 바로 시작하기

1. 위 4주 트랙 중 **1주차 항목을 오늘 30분만 시도**해보세요.
2. 결과(소요시간 단축, 콘텐츠 1건 발행 등)를 **숫자로 기록**해두세요.
3. 한 달 뒤 신화AI부동산 진단을 다시 받아 **숙련도 변화**를 확인해보세요.

---

_본 로드맵은 신화AI부동산이 발행한 **{name} 공인중개사님 ({biz})** 전용 AI 학습 가이드입니다._
_발행일시: {issued_at} · © 신화AI부동산_
"""


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sample = generate_roadmap(
        business_name="OO공인중개사사무소",
        user_name="홍길동",
        main_property=["아파트", "오피스텔"],
        custom_property="분양 + 입주장 업무",
        ai_goals=["블로그·SNS 콘텐츠 자동 작성", "고객 관리(CRM) 자동화"],
        custom_goals="단지 입주민 카톡 단체방 운영 자동화",
        ai_level="3. 기본 활용 — 업무에 가끔 사용",
    )
    print(sample)
