"""
신화AI부동산 — 로드맵 Markdown 텍스트를 한글 PDF로 변환
fpdf2 + NanumGothic 폰트 임베딩
"""
from __future__ import annotations
import re
from io import BytesIO
from pathlib import Path
from fpdf import FPDF

# Windows 시스템 폰트 경로 (대부분의 Windows에 기본 포함)
FONT_REGULAR = Path("C:/Windows/Fonts/NanumGothic.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/NanumGothicBold.ttf")


# NanumGothic이 렌더링하지 못하는 이모지·확장 기호 범위
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"   # 기타 심볼·픽토그램·이모지
    "\U00002600-\U000027BF"   # 기본 심볼 (체크마크 등)
    "\U0001F000-\U0001F2FF"
    "←-⇿"           # 화살표
    "]",
    flags=re.UNICODE,
)


# NanumGothic 글리프에 없는 스마트 따옴표·대시 등을 ASCII로 정규화
_PUNCT_MAP = str.maketrans({
    "‘": "'", "’": "'",   # ‘ ’
    "“": '"', "”": '"',   # “ ”
    "–": "-", "—": "-",   # – —
    "…": "...",                 # …
    " ": " ",                   # NBSP
})


def _safe_multi_cell(pdf, w, h, txt):
    """fpdf2가 그릴 수 없는 문자가 섞여 있어도 죽지 않도록 한 글자씩 시도."""
    try:
        pdf.multi_cell(w, h, txt)
    except Exception:
        # 한 글자씩 안전한 문자만 남기고 재시도
        safe_chars = []
        for ch in txt:
            try:
                pdf.get_string_width(ch)
                safe_chars.append(ch)
            except Exception:
                safe_chars.append(" ")
        try:
            pdf.multi_cell(w, h, "".join(safe_chars).strip() or " ")
        except Exception:
            pdf.ln(h)


def _strip_md(text: str) -> str:
    """이모지·마크다운 표식을 PDF 출력용으로 정리합니다."""
    # 굵게(**text**) / 이탤릭(_text_) 표식 제거
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # NanumGothic으로 못 그리는 이모지·심볼 제거
    text = _EMOJI_RE.sub("", text)
    # 스마트 따옴표/대시를 ASCII로 정규화
    text = text.translate(_PUNCT_MAP)
    # 이모지 제거 후 남은 공백 정리
    text = re.sub(r" {2,}", " ", text)
    return text


def build_pdf(markdown_text: str) -> bytes:
    """
    Markdown 로드맵 텍스트를 받아 PDF 바이트를 반환합니다.
    Streamlit의 st.download_button 의 data 인자로 바로 넘기면 됩니다.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # 한글 폰트 등록
    pdf.add_font("Nanum", "", str(FONT_REGULAR))
    pdf.add_font("Nanum", "B", str(FONT_BOLD))

    # 헤더 (신화AI부동산 브랜딩)
    pdf.set_font("Nanum", "B", 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 12, "신화AI부동산", ln=True, align="C")
    pdf.set_font("Nanum", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "공인중개사 맞춤 AI 학습 로드맵", ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(0.6)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    pdf.set_text_color(20, 20, 20)

    # 본문 — 라인별로 헤더 레벨에 따라 스타일링
    for raw_line in markdown_text.splitlines():
        line = _strip_md(raw_line).rstrip()

        if not line:
            pdf.ln(3)
            continue

        # H1 (#) — PDF 헤더로 이미 출력했으므로 스킵
        if line.startswith("# "):
            continue

        # H2 (##)
        if line.startswith("## "):
            pdf.ln(2)
            pdf.set_font("Nanum", "B", 14)
            pdf.set_text_color(0, 51, 102)
            _safe_multi_cell(pdf,0, 8, line[3:].strip())
            pdf.set_text_color(20, 20, 20)
            continue

        # H3 (###)
        if line.startswith("### "):
            pdf.ln(1)
            pdf.set_font("Nanum", "B", 12)
            pdf.set_text_color(40, 40, 40)
            _safe_multi_cell(pdf,0, 7, line[4:].strip())
            pdf.set_text_color(20, 20, 20)
            continue

        # 인용(>)
        if line.startswith("> "):
            pdf.set_font("Nanum", "", 10)
            pdf.set_text_color(110, 110, 110)
            _safe_multi_cell(pdf,0, 6, "  " + line[2:].strip())
            pdf.set_text_color(20, 20, 20)
            continue

        # 리스트 (- )
        if line.startswith("- "):
            pdf.set_font("Nanum", "", 11)
            _safe_multi_cell(pdf,0, 6.5, "  • " + line[2:].strip())
            continue

        # 구분선
        if line.startswith("---"):
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.2)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)
            continue

        # 일반 본문
        pdf.set_font("Nanum", "", 11)
        _safe_multi_cell(pdf,0, 6.5, line)

    # 출력
    out = pdf.output(dest="S")
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)
