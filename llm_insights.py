"""
신화AI부동산 — 자유 입력 텍스트 LLM 분석 (Claude API)

사용자가 진단 시 자유롭게 입력하는 custom_property / custom_goals 텍스트를
Claude Haiku 4.5 로 분석해 구체적 페인·맞춤 추천을 추출한다.

- API 키 미설정·실패 시 silent fallback (사용자 흐름 영향 0)
- 자유 입력이 모두 비어있으면 호출 안 함 (비용 절감)
- 응답은 JSON 으로 강제, 파싱 실패 시 None
"""
from __future__ import annotations
import json
import logging
import re

import streamlit as st

logger = logging.getLogger(__name__)

# 모델: Haiku 4.5 — 텍스트 분석에 충분히 강력하면서 가장 저렴
MODEL = "claude-haiku-4-5-20251001"
# 한국어 JSON 응답은 토큰 효율이 낮아 (한 글자당 2~3 토큰) 여유 있게 설정
MAX_TOKENS = 1500


def is_llm_active() -> bool:
    """API 키가 secrets 에 설정되어 있고 비어있지 않은지."""
    try:
        key = st.secrets.get("anthropic", {}).get("api_key", "")
        return bool(key and key.strip())
    except Exception:
        return False


def _build_prompt(
    *,
    business_name: str,
    user_name: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> str:
    """LLM 에게 보낼 프롬프트를 구성. JSON 응답 강제."""
    props_str = ", ".join(main_property) if main_property else "(선택 없음)"
    goals_str = ", ".join(ai_goals) if ai_goals else "(선택 없음)"

    return f"""당신은 한국 부동산 중개업 도메인 전문가이자 AI 학습 코치입니다.
공인중개사가 본인의 진단 응답을 제출했습니다. 특히 **자유 입력 텍스트** 를 자세히 분석해
일반적인 매핑으로는 잡히지 않는 **구체적인 페인** 과 **맞춤 추천** 을 한국어로 작성해주세요.

[진단 응답]
- 사업자 상호: {business_name}
- 본인 성함: {user_name}님
- 현재 AI 숙련도: {ai_level}
- 선택한 주력 매물: {props_str}
- 자유 입력 (기타 매물·업무): "{custom_property or '(비어있음)'}"
- 선택한 AI 활용 목표: {goals_str}
- 자유 입력 (기타 AI 목표): "{custom_goals or '(비어있음)'}"

[요청사항]
아래 JSON 형식으로만 응답해주세요. JSON 앞뒤에 다른 텍스트는 절대 포함하지 마세요.

{{
  "summary": "한 단락 (2~3 문장) 의 맞춤 코멘트. {user_name}님께 말씀드리듯 친근하고 정중한 톤. 자유 입력의 핵심 의도를 짚어주고 1~2개의 구체적 방향성을 제시. 일반론 금지.",
  "key_pains": ["자유 입력에서 추출한 핵심 페인 1 (한 문장)", "페인 2 (있을 때만, 없으면 빈 배열)"],
  "tool_recommendations": [
    {{"tool": "도구·콘텐츠·기법명", "reason": "왜 이게 이 분께 매칭되는지 한 문장 — 자유 입력에 근거"}}
  ],
  "instructor_note": "강사가 1:1 컨설팅 준비 시 알아두면 좋을 1줄 노트 — 이 사람의 핵심 페인 요약 (강사 시선)"
}}

[작성 가이드]
- 자유 입력이 둘 다 비어있으면 summary 만 짧게 ("자유 입력이 없어 일반 가이드만 제공됩니다") 처리하고, key_pains·tool_recommendations 는 빈 배열.
- tool_recommendations 는 최대 2개. 가짜 도구·없는 도구 금지. ChatGPT·Claude·Perplexity 같은 대중적 도구 또는 부동산 도메인 실용 도구만.
- 한국 부동산 시장 맥락(공인중개사법·실거래가·임장·매물·계약서 등) 자연스럽게 반영.
- 마크다운 헤더(#, **) 금지, 순수 JSON 만."""


def _parse_response(text: str) -> dict | None:
    """LLM 응답 텍스트에서 JSON 추출 후 파싱.

    응답에 코드 펜스(```json ... ```) 가 섞여 있을 수 있어 정규식으로 첫 { 부터 마지막 } 까지 추출.
    """
    if not text:
        return None
    # JSON 본문 추출 (가장 바깥 중괄호 쌍)
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.warning("LLM JSON 파싱 실패: %s", e)
        return None

    # 필수 키 보정 (LLM 이 일부 누락해도 안전)
    return {
        "summary": str(data.get("summary") or "").strip(),
        "key_pains": [str(p).strip() for p in (data.get("key_pains") or []) if str(p).strip()],
        "tool_recommendations": [
            {
                "tool": str(t.get("tool") or "").strip(),
                "reason": str(t.get("reason") or "").strip(),
            }
            for t in (data.get("tool_recommendations") or [])
            if isinstance(t, dict) and t.get("tool")
        ],
        "instructor_note": str(data.get("instructor_note") or "").strip(),
    }


def generate_custom_insights(
    *,
    business_name: str,
    user_name: str,
    main_property: list[str],
    custom_property: str,
    ai_goals: list[str],
    custom_goals: str,
    ai_level: str,
) -> dict | None:
    """자유 입력 기반 LLM 인사이트 추출.

    Returns:
        {
          "summary": str,                  # 한 단락 맞춤 코멘트
          "key_pains": list[str],          # 핵심 페인 0~2개
          "tool_recommendations": list[{"tool":str, "reason":str}],
          "instructor_note": str,          # 강사용 한 줄 노트
        }
        또는 None — API 키 없음 / 자유 입력 모두 빈 값 / API 호출·파싱 실패.
    """
    if not is_llm_active():
        return None

    # 자유 입력이 모두 비어있으면 비용 절감을 위해 호출하지 않음
    if not (custom_property.strip() or custom_goals.strip()):
        return None

    try:
        from anthropic import Anthropic
    except ImportError:
        logger.warning("anthropic 패키지 미설치 — requirements.txt 에 추가되어 Streamlit Cloud 는 자동 설치됨")
        return None

    try:
        api_key = st.secrets["anthropic"]["api_key"]
        client = Anthropic(api_key=api_key)
        prompt = _build_prompt(
            business_name=business_name,
            user_name=user_name,
            main_property=main_property,
            custom_property=custom_property,
            ai_goals=ai_goals,
            custom_goals=custom_goals,
            ai_level=ai_level,
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        # 응답 잘림 감지 — max_tokens 한계로 JSON 끝이 잘리면 파싱 실패 가능
        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason == "max_tokens":
            logger.warning("Claude 응답이 max_tokens 한계로 잘림 — MAX_TOKENS 증액 검토 필요")

        # response.content 는 ContentBlock 리스트. 첫 텍스트 블록 추출.
        text = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text = block.text
                break
        return _parse_response(text)
    except Exception as e:
        # 네트워크·인증·모델 에러 등 모두 silent fallback
        logger.warning("Claude API 호출 실패: %s", e)
        return None
