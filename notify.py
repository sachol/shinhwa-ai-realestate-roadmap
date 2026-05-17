"""
신화AI부동산 — 수강생 진단 제출 시 강사에게 이메일 알림 (Gmail SMTP)

필요한 secrets (.streamlit/secrets.toml):
[notify]
sender_email      = "sachol.cap@gmail.com"        # 발송자 Gmail
sender_app_pw     = "abcd efgh ijkl mnop"          # 16자리 앱 비밀번호 (공백 포함 가능)
recipients        = ["sachol.cap@gmail.com"]       # 수신자 리스트
smtp_host         = "smtp.gmail.com"               # 선택, 기본값
smtp_port         = 587                            # 선택, 기본값

설정이 없거나 발송 실패해도 학습자 흐름은 절대 막지 않습니다 (조용히 로그만 남김).
"""
from __future__ import annotations
import re
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from email.header import Header

import streamlit as st

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

logger = logging.getLogger(__name__)


def _read_notify_config() -> dict | None:
    """secrets에서 알림 설정을 읽어옴. 미설정 시 None."""
    try:
        if "notify" not in st.secrets:
            return None
        cfg = dict(st.secrets["notify"])
    except Exception:
        return None

    sender = (cfg.get("sender_email") or "").strip()
    pw = (cfg.get("sender_app_pw") or "").strip().replace(" ", "")
    recipients = cfg.get("recipients") or []
    if isinstance(recipients, str):
        recipients = [recipients]
    recipients = [r.strip() for r in recipients if r and str(r).strip()]

    if not sender or not pw or not recipients:
        return None

    return {
        "sender": sender,
        "password": pw,
        "recipients": recipients,
        "smtp_host": cfg.get("smtp_host", "smtp.gmail.com"),
        "smtp_port": int(cfg.get("smtp_port", 587)),
    }


def is_notify_active() -> bool:
    return _read_notify_config() is not None


def _build_html(payload: dict, sheet_link: str | None) -> str:
    def _join(v):
        if isinstance(v, list):
            return ", ".join(v) if v else "<em>(없음)</em>"
        return v or "<em>(없음)</em>"

    sheet_html = (
        f'<p style="margin-top:18px;"><a href="{sheet_link}" '
        f'style="background:#0F3D77;color:#fff;text-decoration:none;'
        f'padding:8px 14px;border-radius:6px;display:inline-block;">'
        f'📊 응답 시트에서 자세히 보기</a></p>'
        if sheet_link
        else ""
    )

    return f"""\
<!doctype html>
<html><body style="font-family:Apple SD Gothic Neo,Malgun Gothic,Arial,sans-serif;
                    color:#1B2330; max-width:640px; margin:0 auto; padding:0;">
  <div style="background:linear-gradient(135deg,#0F3D77,#1B5BB0);
              color:#fff; padding:18px 22px; border-radius:12px 12px 0 0;">
    <div style="font-size:13px; letter-spacing:.4px; opacity:.85;">신화AI부동산 · 진단 제출 알림</div>
    <div style="font-size:20px; font-weight:700; margin-top:4px;">
      새 수강생 진단 응답이 도착했습니다 🎯
    </div>
  </div>
  <div style="background:#fff; border:1px solid #E6EAF0; border-top:none;
              border-radius:0 0 12px 12px; padding:22px;">
    <table style="width:100%; border-collapse:collapse; font-size:14px;">
      <tr><td style="padding:6px 0; color:#6B7686; width:120px;">응답 ID</td>
          <td style="padding:6px 0;"><b>#{payload.get('id', '-')}</b></td></tr>
      <tr><td style="padding:6px 0; color:#6B7686;">제출 시각</td>
          <td style="padding:6px 0;">{payload.get('submitted_at', '-')}</td></tr>
      <tr><td style="padding:6px 0; color:#6B7686;">사업자 상호</td>
          <td style="padding:6px 0;"><b>{payload.get('business_name', '-')}</b></td></tr>
      <tr><td style="padding:6px 0; color:#6B7686;">성함</td>
          <td style="padding:6px 0;"><b>{payload.get('user_name', '-')}</b></td></tr>
      <tr><td style="padding:6px 0; color:#6B7686;">이메일</td>
          <td style="padding:6px 0;">
            <a href="mailto:{payload.get('email','')}">{payload.get('email','-')}</a>
          </td></tr>
      <tr><td style="padding:6px 0; color:#6B7686;">AI 숙련도</td>
          <td style="padding:6px 0;">{payload.get('ai_level', '-')}</td></tr>
    </table>

    <hr style="border:none; border-top:1px solid #EEF1F6; margin:14px 0;">

    <div style="font-size:13px;">
      <div style="color:#6B7686; margin-bottom:4px;">주력 매물</div>
      <div style="margin-bottom:10px;">{_join(payload.get('main_property'))}</div>

      <div style="color:#6B7686; margin-bottom:4px;">기타 매물·업무 (직접 입력)</div>
      <div style="margin-bottom:10px;">{_join(payload.get('custom_property'))}</div>

      <div style="color:#6B7686; margin-bottom:4px;">AI 활용 목표</div>
      <div style="margin-bottom:10px;">{_join(payload.get('ai_goals'))}</div>

      <div style="color:#6B7686; margin-bottom:4px;">기타 업무 (직접 입력)</div>
      <div style="margin-bottom:10px;">{_join(payload.get('custom_goals'))}</div>
    </div>

    {sheet_html}

    <p style="font-size:12px; color:#8A95A6; margin-top:22px;">
      이 메일은 신화AI부동산 진단 웹앱이 자동 발송한 알림입니다.
    </p>
  </div>
</body></html>
"""


def _sheet_link() -> str | None:
    try:
        if "sheets" in st.secrets and "spreadsheet_id" in st.secrets["sheets"]:
            sid = st.secrets["sheets"]["spreadsheet_id"]
            return f"https://docs.google.com/spreadsheets/d/{sid}/edit"
    except Exception:
        pass
    return None


def send_admin_notification(payload: dict) -> bool:
    """
    payload 예:
    {
        "id": 12, "submitted_at": "2026-05-17 18:42:11",
        "business_name": "신화공인", "user_name": "홍길동",
        "email": "hong@x.com", "ai_level": "3. 기본 활용 ...",
        "main_property": [...], "custom_property": "...",
        "ai_goals": [...], "custom_goals": "...",
    }
    """
    cfg = _read_notify_config()
    if cfg is None:
        logger.info("notify: secrets 미설정 — 메일 발송 건너뜀")
        return False

    subject = (
        f"[신화AI부동산] 새 진단 #{payload.get('id', '?')} · "
        f"{payload.get('business_name', '-')} / {payload.get('user_name', '-')}"
    )
    html_body = _build_html(payload, _sheet_link())

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("신화AI부동산 진단 봇", cfg["sender"]))
    msg["To"] = ", ".join(cfg["recipients"])
    msg.attach(MIMEText("HTML 메일 클라이언트에서 열어주세요.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ctx)
            smtp.login(cfg["sender"], cfg["password"])
            smtp.sendmail(cfg["sender"], cfg["recipients"], msg.as_string())
        return True
    except Exception as e:
        logger.error(f"notify: 메일 발송 실패 — {e}")
        return False


# ─────────────────────────────────────────────
# 수강생용: 진단 결과 PDF 첨부 메일 발송
# ─────────────────────────────────────────────
APP_URL = "https://shinhwa-ai-realestate-roadmap-rsaaiforumfighting.streamlit.app/"


def _build_student_html(payload: dict) -> str:
    def _join(v):
        if isinstance(v, list):
            return ", ".join(v) if v else "<em style='color:#A0A8B5;'>(없음)</em>"
        return v or "<em style='color:#A0A8B5;'>(없음)</em>"

    name = payload.get("user_name", "공인중개사")
    biz = payload.get("business_name", "")

    return f"""\
<!doctype html>
<html><body style="font-family:Apple SD Gothic Neo,Malgun Gothic,Arial,sans-serif;
                    color:#1B2330; max-width:640px; margin:0 auto; padding:0;
                    background:#F4F7FB;">
  <div style="background:linear-gradient(135deg,#0F3D77,#1B5BB0);
              color:#fff; padding:24px 22px; border-radius:12px 12px 0 0;">
    <div style="font-size:12px; letter-spacing:.4px; opacity:.85;">
      신화AI부동산 · 공인중개사 AI 학습 진단
    </div>
    <div style="font-size:22px; font-weight:700; margin-top:6px;">
      {name} 공인중개사님, 진단 결과를 보내드립니다 🎯
    </div>
  </div>

  <div style="background:#fff; border:1px solid #E6EAF0; border-top:none;
              padding:24px 22px; line-height:1.65;">
    <p style="margin-top:0;">
      <b>{biz}</b>의 <b>{name}</b>님,<br>
      신화AI부동산 진단을 완료해주셔서 감사합니다.<br>
      입력해주신 정보를 바탕으로 맞춤 AI 학습 로드맵을
      <b>PDF 파일로 첨부</b>해 보내드립니다.
    </p>

    <div style="background:#F4F7FB; border-left:4px solid #0F3D77;
                padding:14px 16px; margin:18px 0; border-radius:6px;">
      <div style="font-size:13px; color:#6B7686; margin-bottom:6px;">📋 진단 요약</div>
      <div style="font-size:14px;">
        <div><b>숙련도</b> · {payload.get('ai_level', '-')}</div>
        <div style="margin-top:4px;"><b>주력 매물</b> · {_join(payload.get('main_property'))}</div>
        <div style="margin-top:4px;"><b>AI 활용 목표</b> · {_join(payload.get('ai_goals'))}</div>
      </div>
    </div>

    <p style="font-size:14px;">
      📎 <b>첨부 PDF</b>에서 상세한 추천 도구와
      <b>4주 학습 트랙</b>을 확인하실 수 있습니다.<br>
      한 달 뒤 다시 진단받으시면 본인의 성장 정도를 측정해보실 수 있습니다.
    </p>

    <p style="text-align:center; margin:24px 0 14px 0;">
      <a href="{APP_URL}"
         style="background:#FFB400; color:#0F3D77; text-decoration:none;
                padding:11px 22px; border-radius:8px; font-weight:700;
                display:inline-block; font-size:14px;">
        🔄 다시 진단받기
      </a>
    </p>

    <hr style="border:none; border-top:1px solid #EEF1F6; margin:20px 0;">

    <p style="font-size:11.5px; color:#8A95A6; line-height:1.6;">
      ⚖️ <b>면책 안내</b><br>
      본 결과물은 일반적인 정보 제공·교육 목적의 참고자료이며,
      법률·세무·금융·투자 자문이 아닙니다.
      본 내용을 활용해 발생한 모든 의사결정과 그 결과는 사용자 본인의 책임이며,
      신화AI부동산은 어떠한 책임도 지지 않습니다.
      각 도구의 이용 약관·요금·개인정보 처리 방침은 사용자 본인이 직접 확인해주세요.
    </p>

    <p style="font-size:11.5px; color:#8A95A6; margin-top:14px;">
      이 메일은 신화AI부동산 진단 웹앱이 자동 발송한 메일입니다.<br>
      문의 회신은 그대로 답장하시면 됩니다.
    </p>
  </div>

  <div style="text-align:center; padding:14px; font-size:11px; color:#8A95A6;">
    © 신화AI부동산 — 공인중개사를 위한 AI 컨설팅 도구
  </div>
</body></html>
"""


def send_student_pdf(payload: dict, pdf_bytes: bytes, filename: str) -> bool:
    """
    수강생 본인 이메일로 진단 결과 PDF를 첨부 발송.
    payload는 send_admin_notification과 동일 형식.
    이메일 주소가 유효하지 않으면 False (조용히 스킵).
    """
    cfg = _read_notify_config()
    if cfg is None:
        return False

    student_email = (payload.get("email") or "").strip()
    if not student_email or not EMAIL_RE.match(student_email):
        logger.info(f"notify: 유효하지 않은 수강생 이메일 — {student_email!r}")
        return False

    name = payload.get("user_name", "공인중개사")
    subject = f"[신화AI부동산] {name}님의 AI 학습 로드맵 진단 결과"

    msg = MIMEMultipart("mixed")
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg["From"] = formataddr((str(Header("신화AI부동산", "utf-8")), cfg["sender"]))
    msg["To"] = student_email
    msg["Reply-To"] = cfg["sender"]

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(
        f"{name} 공인중개사님,\n\n"
        f"신화AI부동산 진단 결과를 첨부 PDF로 보내드립니다.\n"
        f"HTML 메일 클라이언트에서 열어주시면 더 보기 좋게 표시됩니다.\n\n"
        f"한 달 뒤 다시 진단받기: {APP_URL}\n\n"
        f"© 신화AI부동산",
        "plain", "utf-8",
    ))
    body.attach(MIMEText(_build_student_html(payload), "html", "utf-8"))
    msg.attach(body)

    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header(
        "Content-Disposition", "attachment",
        filename=("utf-8", "", filename),
    )
    msg.attach(pdf_part)

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ctx)
            smtp.login(cfg["sender"], cfg["password"])
            smtp.sendmail(cfg["sender"], [student_email], msg.as_string())
        return True
    except Exception as e:
        logger.error(f"notify: 수강생 메일 발송 실패 — {e}")
        return False
