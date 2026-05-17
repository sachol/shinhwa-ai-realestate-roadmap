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


def build_pdf(markdown_text: str) -> bytes:
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
