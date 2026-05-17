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
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Iterable

import streamlit as st

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
