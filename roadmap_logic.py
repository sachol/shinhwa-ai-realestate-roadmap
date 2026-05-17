"""
신화AI부동산 — 공인중개사 맞춤형 AI 학습 로드맵 생성 로직
설문 3축 (주력 매물 / AI 활용 목표 / 숙련도)을 입력받아 텍스트 로드맵을 반환합니다.
"""
from __future__ import annotations
from datetime import datetime

# ─────────────────────────────────────────────
# 1) AI 활용 목표 → 추천 도구 매핑
# ─────────────────────────────────────────────
GOAL_TO_TOOLS: dict[str, list[dict]] = {
    "블로그·SNS 콘텐츠 자동 작성": [
        {"name": "ChatGPT / Claude", "why": "매물 소개 글, 블로그 포스팅 초안을 1분 만에 생성"},
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
        {"name": "카카오톡 챗봇 빌더 (채널톡 등)", "why": "실 채널에 연결해 1차 응대 자동화"},
        {"name": "Claude Projects", "why": "고객별 상담 이력·메모를 한 공간에서 관리"},
    ],
    "광고 카피·문구 제작": [
        {"name": "ChatGPT / Claude", "why": "매물별 광고 카피 A/B안을 즉시 생성"},
        {"name": "뤼튼 (Wrtn)", "why": "한국어 광고 문구·블로그 카피에 특화"},
        {"name": "Midjourney / DALL·E", "why": "광고용 시각 컨셉 이미지 생성"},
    ],
}

# ─────────────────────────────────────────────
# 2) 주력 매물 → 활용 예시 톤 (사례 한 줄씩)
# ─────────────────────────────────────────────
PROPERTY_HOOKS: dict[str, str] = {
    "아파트": "예: 동일 단지·평형 실거래 추이를 Claude에 붙여넣고 “지난 6개월 동향 요약해줘”라고 물어보세요.",
    "상가": "예: 상권 유동인구·업종 분포 데이터를 AI에 분석시켜 ‘이 자리에 어떤 업종이 가장 적합한가’ 인사이트를 받아보세요.",
    "토지": "예: 용도지역·지목·공시지가를 표로 정리해 AI에게 ‘투자 매력도 점수’를 매겨달라고 요청해보세요.",
    "빌라·다세대": "예: 동일 권역 빌라 거래량·전세가율을 AI로 비교 분석해 매도/매수 타이밍 리포트를 만들어보세요.",
}

# ─────────────────────────────────────────────
# 3) 숙련도 → 학습 순서 트랙
# ─────────────────────────────────────────────
LEVEL_TRACKS: dict[str, list[str]] = {
    "하 (입문)": [
        "1주차: ChatGPT 또는 Claude 무료 계정 만들고, 매물 소개 글 한 편 써보기",
        "2주차: 프롬프트 작성법 기본 — ‘역할·맥락·요구사항’ 3박자 익히기",
        "3주차: 자주 쓰는 업무 5개를 골라 ‘나만의 프롬프트 템플릿’ 만들기",
        "4주차: 실제 업무 1건을 AI와 함께 처리해 시간 단축 효과 측정",
    ],
    "중 (기본 사용 가능)": [
        "1주차: 유료 플랜(ChatGPT Plus 또는 Claude Pro) 도입 + 커스텀 GPT/Projects 활용",
        "2주차: 공공데이터·실거래가 API를 Claude/Excel과 연동해 자동 보고서 만들기",
        "3주차: 블로그·SNS 콘텐츠 발행 자동화 워크플로 설계",
        "4주차: 고객 1차 응대 챗봇 프로토타입 구축",
    ],
    "상 (능숙)": [
        "1주차: Claude Code · MCP Server로 본인 DB/CRM에 직접 연결하는 자동화 구축",
        "2주차: Agent Teams 패턴으로 ‘리서처 + 카피라이터 + 디자이너’ AI 팀 구성",
        "3주차: Streamlit 같은 도구로 사내·고객용 AI 진단 웹앱 직접 제작",
        "4주차: AI 컨설팅 결과를 동료 중개사에게 교육·전파하는 콘텐츠화",
    ],
}


def _format_tools_section(ai_goals: list[str]) -> str:
    if not ai_goals:
        return "_(AI 활용 목표가 선택되지 않았습니다.)_"
    lines: list[str] = []
    for goal in ai_goals:
        lines.append(f"\n### 🎯 목표: {goal}")
        for tool in GOAL_TO_TOOLS.get(goal, []):
            lines.append(f"- **{tool['name']}** — {tool['why']}")
    return "\n".join(lines)


def _format_track(ai_level: str) -> str:
    track = LEVEL_TRACKS.get(ai_level, [])
    return "\n".join(f"- {item}" for item in track)


def generate_roadmap(
    main_property: str,
    ai_goals: list[str],
    ai_level: str,
) -> str:
    """
    설문 답변을 받아 공인중개사 맞춤 학습 로드맵 텍스트(Markdown)를 반환합니다.

    Args:
        main_property: 주력 매물 종류 (예: "아파트")
        ai_goals: AI 활용 목표 리스트 (복수 선택)
        ai_level: AI 숙련도 ("하 (입문)" | "중 (기본 사용 가능)" | "상 (능숙)")
    """
    hook = PROPERTY_HOOKS.get(main_property, "")
    today = datetime.now().strftime("%Y년 %m월 %d일")

    roadmap = f"""# 🏠 신화AI부동산 맞춤 AI 학습 로드맵

> **발행일**: {today}
> **대상**: 주력 매물 **{main_property}** / 숙련도 **{ai_level}**

---

## 1. 진단 요약

공인중개사님은 현재 **{ai_level}** 수준에서 **{main_property}** 매물을 다루고 계시며,
다음 영역에서 AI를 활용하고자 하십니다:

{', '.join(f'**{g}**' for g in ai_goals) if ai_goals else '_(미선택)_'}

> 💡 **{main_property} 중개사를 위한 한 줄 활용 팁**
> {hook}

---

## 2. 목표별 추천 AI 도구
{_format_tools_section(ai_goals)}

---

## 3. 4주 학습 트랙 (숙련도 **{ai_level}** 기준)

{_format_track(ai_level)}

---

## 4. 다음 액션 — 오늘 바로 시작하기

1. 위 4주 트랙 중 **1주차 항목을 오늘 30분만 시도**해보세요.
2. 결과(소요시간 단축, 콘텐츠 1건 발행 등)를 **숫자로 기록**해두세요.
3. 한 달 뒤 신화AI부동산 진단을 다시 받아 **숙련도 변화**를 확인해보세요.

---

_본 로드맵은 신화AI부동산이 제작한 공인중개사 전용 AI 학습 가이드입니다._
_© 신화AI부동산_
"""
    return roadmap


# ─────────────────────────────────────────────
# 간단 자체 테스트
# ─────────────────────────────────────────────
if __name__ == "__main__":
    sample = generate_roadmap(
        main_property="아파트",
        ai_goals=["블로그·SNS 콘텐츠 자동 작성", "매물 시세·입지 분석"],
        ai_level="중 (기본 사용 가능)",
    )
    print(sample)
