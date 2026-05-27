"""
신화AI부동산 — 로드맵 Markdown 텍스트를 한글 PDF로 변환
fpdf2 + NanumGothic 폰트 임베딩
"""
from __future__ import annotations
import re
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# 폰트 우선순위: 저장소 내 fonts/ → Windows 시스템 폰트 (로컬 개발 폴백)
_BUNDLED = Path(__file__).parent / "fonts"
_SYSTEM_WIN = Path("C:/Windows/Fonts")


def _pick_font(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"한글 폰트를 찾을 수 없습니다. 후보: {[str(c) for c in candidates]}"
    )


FONT_REGULAR = _pick_font(
    _BUNDLED / "NanumGothic.ttf",
    _SYSTEM_WIN / "NanumGothic.ttf",
)
FONT_BOLD = _pick_font(
    _BUNDLED / "NanumGothicBold.ttf",
    _SYSTEM_WIN / "NanumGothicBold.ttf",
    _BUNDLED / "NanumGothic.ttf",
    _SYSTEM_WIN / "NanumGothic.ttf",
)

# NanumGothic이 렌더링하지 못하는 이모지·확장 기호 범위
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F2FF"
    "←-⇿"
    "]",
    flags=re.UNICODE,
)

_PUNCT_MAP = str.maketrans({
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "–": "-", "—": "-",
    "…": "...",
    " ": " ",
})


def _normalize(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = _EMOJI_RE.sub("", text)
    text = text.translate(_PUNCT_MAP)
    text = re.sub(r" {2,}", " ", text)
    return text


def _write_block(pdf: FPDF, text: str, line_h: float) -> None:
    """텍스트 한 블록을 안전하게 multi_cell로 출력. 커서를 다음 줄로 명시 이동."""
    if not text.strip():
        pdf.ln(line_h)
        return
    try:
        pdf.multi_cell(
            w=0, h=line_h, text=text,
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
    except Exception:
        # 글리프 없는 문자가 섞여 있으면 문자별로 거를 수 있는 것만 남김
        safe = []
        for ch in text:
            try:
                pdf.get_string_width(ch)
                safe.append(ch)
            except Exception:
                safe.append(" ")
        cleaned = re.sub(r" {2,}", " ", "".join(safe)).strip()
        if cleaned:
            try:
                pdf.multi_cell(
                    w=0, h=line_h, text=cleaned,
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )
            except Exception:
                # 마지막 폴백: 줄 비우기보다 placeholder 한 줄
                pdf.multi_cell(
                    w=0, h=line_h, text="(표시 불가)",
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )
        else:
            pdf.ln(line_h)


# ─────────────────────────────────────────────────────────────────────────
# 재진단 비교 페이지 렌더링 (2026-05-27 추가) — markdown 우회, fpdf2 직접 호출
# UI 의 render_comparison_card 에 대응하는 PDF 전용 디자인 (컬러 박스·표·배지)
# ─────────────────────────────────────────────────────────────────────────

_CMP_BG_GROWTH = (220, 252, 231)   # 연한 녹색 — 성장 헤드라인 배경
_CMP_FG_GROWTH = (22, 101, 52)     # 짙은 녹색 — 성장 텍스트
_CMP_BG_DECLINE = (224, 232, 245)  # 연한 남색 — 하락·동일 헤드라인 배경
_CMP_FG_DECLINE = (15, 61, 119)    # 짙은 남색 — 하락 텍스트·섹션 제목
_CMP_BG_NEUTRAL = (243, 244, 246)  # 연한 회색 — 표 헤더·뉴트럴
_CMP_BG_ADD = (220, 252, 231)
_CMP_FG_ADD = (22, 101, 52)
_CMP_BG_REMOVE = (251, 233, 231)
_CMP_FG_REMOVE = (139, 22, 22)
_CMP_BG_KEEP = (224, 232, 245)
_CMP_FG_KEEP = (15, 61, 119)


def _render_diff_section_pdf(pdf: FPDF, title: str, diff: dict) -> None:
    """추가·제외·유지 섹션 한 블록을 PDF 에 그린다 (배지 + 들여쓰기 아이템 리스트)."""
    pdf.set_font("Nanum", "B", 13)
    pdf.set_text_color(*_CMP_FG_DECLINE)
    pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(20, 20, 20)
    pdf.ln(2)

    items = [
        ("+ 추가", diff.get("added") or [], _CMP_BG_ADD, _CMP_FG_ADD),
        ("- 제외", diff.get("removed") or [], _CMP_BG_REMOVE, _CMP_FG_REMOVE),
        ("= 유지", diff.get("kept") or [], _CMP_BG_KEEP, _CMP_FG_KEEP),
    ]
    rendered = False
    for label, lst, bg, fg in items:
        if not lst:
            continue
        rendered = True
        # 컬러 배지
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*fg)
        pdf.set_font("Nanum", "B", 10)
        badge_text = f"  {label} ({len(lst)})  "
        badge_width = pdf.get_string_width(badge_text) + 4
        pdf.cell(
            w=badge_width, h=7, text=badge_text, fill=True,
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        # 아이템 (들여쓰기 + 자동 줄바꿈)
        pdf.set_font("Nanum", "", 10)
        pdf.set_text_color(40, 40, 40)
        items_text = ", ".join(str(item) for item in lst)
        pdf.multi_cell(
            w=180, h=6, text="    " + items_text,
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.ln(2)
        pdf.set_text_color(20, 20, 20)

    if not rendered:
        pdf.set_font("Nanum", "", 10)
        pdf.set_text_color(110, 110, 110)
        pdf.cell(0, 7, "    (변화 없음)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(20, 20, 20)
    pdf.ln(4)


def _render_comparison_section(
    pdf: FPDF, comparison: dict, total_visits: int
) -> None:
    """build_comparison() 결과를 PDF 첫 페이지에 디자인된 형태로 렌더링.

    Args:
        pdf: 이미 add_page() + 헤더 그려진 FPDF 인스턴스.
        comparison: build_comparison() 의 반환값.
        total_visits: 같은 이메일의 누적 진단 횟수 (현재 포함).
    """
    level = comparison.get("level") or {}
    delta = level.get("delta")
    days = comparison.get("days_between")

    # ── 큰 헤더 ──
    pdf.set_font("Nanum", "B", 16)
    pdf.set_text_color(*_CMP_FG_DECLINE)
    pdf.cell(0, 10, "이전 진단과 비교", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # ── 헤드라인 컬러 박스 (성장/하락 톤) ──
    if delta is not None and delta > 0:
        bg, fg = _CMP_BG_GROWTH, _CMP_FG_GROWTH
        title = f"한 단계씩 성장 중!  숙련도 {delta}단계 상승하셨습니다."
    elif delta is not None and delta < 0:
        bg, fg = _CMP_BG_DECLINE, _CMP_FG_DECLINE
        title = "다시 한 번 차근차근 - 직전보다 숙련도 응답을 보수적으로 잡으셨네요."
    else:
        bg, fg = _CMP_BG_NEUTRAL, _CMP_FG_DECLINE
        title = "꾸준히 진단받고 계시네요. 변화 흐름을 같이 살펴보세요."

    sub_parts = []
    if days is not None:
        sub_parts.append(f"{days}일 경과")
    sub_parts.append(f"{total_visits}번째 진단")
    sub_line = " · ".join(sub_parts)

    pdf.set_fill_color(*bg)
    pdf.set_text_color(*fg)
    pdf.set_font("Nanum", "B", 12)
    pdf.multi_cell(
        w=180, h=8, text="  " + title, fill=True,
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_font("Nanum", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        w=180, h=6, text="  " + sub_line, fill=True,
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_text_color(20, 20, 20)
    pdf.ln(8)

    # ── 숙련도 변화 섹션 (좌·우 표 + 가운데 큰 강조) ──
    pdf.set_font("Nanum", "B", 13)
    pdf.set_text_color(*_CMP_FG_DECLINE)
    pdf.cell(0, 8, "숙련도 변화", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(20, 20, 20)
    pdf.ln(1)

    prev_lbl = (level.get("prev_label") or "(이전 기록 없음)")[:38]
    cur_lbl = (level.get("current_label") or "(현재 기록 없음)")[:38]

    # 표 헤더
    pdf.set_font("Nanum", "B", 10)
    pdf.set_fill_color(*_CMP_BG_NEUTRAL)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(w=90, h=8, text="  이전", border=1, fill=True,
             new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(w=90, h=8, text="  현재", border=1, fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    # 표 본문
    pdf.set_font("Nanum", "", 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(w=90, h=10, text="  " + prev_lbl, border=1,
             new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(w=90, h=10, text="  " + cur_lbl, border=1,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(2)

    # 큰 강조 (가운데 정렬)
    if delta is None:
        delta_text = "(비교 가능한 정보 없음)"
        delta_color = (110, 110, 110)
    elif delta > 0:
        delta_text = f"▲   +{delta}단계 상승"
        delta_color = _CMP_FG_GROWTH
    elif delta < 0:
        delta_text = f"▼   {delta}단계"
        delta_color = _CMP_FG_DECLINE
    else:
        delta_text = "=  동일 단계 유지"
        delta_color = (110, 110, 110)

    pdf.set_font("Nanum", "B", 18)
    pdf.set_text_color(*delta_color)
    pdf.cell(0, 14, delta_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(20, 20, 20)
    pdf.ln(2)

    # 구분선
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # ── 매물 변화 섹션 ──
    _render_diff_section_pdf(pdf, "주력 매물 변화", comparison.get("properties") or {})

    pdf.set_draw_color(200, 200, 200)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # ── 목표 변화 섹션 ──
    _render_diff_section_pdf(pdf, "AI 활용 목표 변화", comparison.get("goals") or {})


def build_pdf(
    markdown_text: str,
    comparison: dict | None = None,
    total_visits: int | None = None,
) -> bytes:
    """로드맵 markdown 을 한글 PDF 로 변환.

    Args:
        markdown_text: 로드맵 본문 markdown.
        comparison: 재진단자라면 build_comparison() 결과. None 이면 비교 페이지 미렌더링.
        total_visits: 재진단자의 누적 진단 횟수 (현재 포함). comparison 와 세트.

    Returns:
        PDF 바이트.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.add_font("Nanum", "", str(FONT_REGULAR))
    pdf.add_font("Nanum", "B", str(FONT_BOLD))

    # 헤더
    pdf.set_font("Nanum", "B", 18)
    pdf.set_text_color(15, 61, 119)
    pdf.cell(0, 12, "신화AI부동산",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Nanum", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "공인중개사 맞춤 AI 학습 로드맵",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)
    pdf.set_draw_color(15, 61, 119)
    pdf.set_line_width(0.6)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    pdf.set_text_color(20, 20, 20)

    # ── 재진단자 전용: 비교 페이지 렌더링 후 새 페이지에서 로드맵 시작 ──
    if comparison is not None and total_visits is not None:
        _render_comparison_section(pdf, comparison, total_visits)
        pdf.add_page()
        # 새 페이지에 헤더 다시 그리기 (작게)
        pdf.set_font("Nanum", "B", 13)
        pdf.set_text_color(15, 61, 119)
        pdf.cell(0, 8, "신화AI부동산 맞춤 AI 학습 로드맵",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(2)
        pdf.set_draw_color(15, 61, 119)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(20, 20, 20)

    for raw in markdown_text.splitlines():
        line = _normalize(raw).rstrip()

        # 빈 줄
        if not line:
            pdf.ln(3)
            continue

        # H1은 헤더로 이미 출력했으므로 스킵
        if line.startswith("# "):
            continue

        # 구분선
        if line.startswith("---"):
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.2)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)
            continue

        # H2
        if line.startswith("## "):
            pdf.ln(2)
            pdf.set_font("Nanum", "B", 14)
            pdf.set_text_color(15, 61, 119)
            _write_block(pdf, line[3:].strip(), 8)
            pdf.set_text_color(20, 20, 20)
            continue

        # H3
        if line.startswith("### "):
            pdf.ln(1)
            pdf.set_font("Nanum", "B", 12)
            pdf.set_text_color(40, 40, 40)
            _write_block(pdf, line[4:].strip(), 7)
            pdf.set_text_color(20, 20, 20)
            continue

        # 인용 (>)
        if line.startswith("> "):
            pdf.set_font("Nanum", "", 10)
            pdf.set_text_color(110, 110, 110)
            _write_block(pdf, "  " + line[2:].strip(), 6)
            pdf.set_text_color(20, 20, 20)
            continue

        # 리스트 (- 또는 숫자.)
        if line.startswith("- "):
            pdf.set_font("Nanum", "", 11)
            _write_block(pdf, "  • " + line[2:].strip(), 6.5)
            continue
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m:
            pdf.set_font("Nanum", "", 11)
            _write_block(pdf, f"  {m.group(1)}. {m.group(2)}", 6.5)
            continue

        # 일반 본문
        pdf.set_font("Nanum", "", 11)
        _write_block(pdf, line, 6.5)

    out = pdf.output()
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)
