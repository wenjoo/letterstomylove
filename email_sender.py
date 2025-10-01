# -*- coding: utf-8 -*-
"""
email_sender.py — HTML email with a SURPRISE button (点我查看 🎁)
- Hard-coded PAGE_URL to your GitHub Pages link
- Time gate: sends only in specific windows unless FORCE_SEND=true
- Supports multiple recipients via RECEIVER_EMAILS (comma-separated)

Supported events (Asia/Kuala_Lumpur):
  - 2025-12-06 05:20 ±10min  ->  纪念日
  - 2026-01-01 00:00 ±10min  ->  跨年

Required secrets (env):
  SENDER_EMAIL, APP_PASSWORD, (RECEIVER_EMAIL or RECEIVER_EMAILS),
  START_DATE, HER_NAME
Optional:
  FORCE_SEND ("true"/"false"),
  FORCE_EVENT ("anniv2025" | "newyear2026"),
  SMTP_SERVER/PORT/USERNAME/PASSWORD for custom SMTP
"""

import os, smtplib, ssl, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Optional

# ===== Your public page (hard-coded) =====
PAGE_URL = os.environ.get("PAGE_URL", "https://wenjoo.github.io/letterstomylove/").strip() or "https://wenjoo.github.io/letterstomylove/"

# ===== Secrets / config =====
SENDER_EMAIL   = os.environ.get("SENDER_EMAIL", "").strip()
APP_PASSWORD   = os.environ.get("APP_PASSWORD", "").strip()

_raw_multi = os.environ.get("RECEIVER_EMAILS", "")
RECEIVER_EMAILS = [e.strip() for e in _raw_multi.split(",") if e.strip()]
if not RECEIVER_EMAILS:
    one = os.environ.get("RECEIVER_EMAIL", "").strip()
    if one: RECEIVER_EMAILS = [one]

START_DATE = os.environ.get("START_DATE", "2022-12-06").strip()
HER_NAME   = os.environ.get("HER_NAME", "Baby").strip()

# SMTP (Gmail by default; supports SendGrid etc. via overrides)
SMTP_SERVER   = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", SENDER_EMAIL).strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", APP_PASSWORD).strip()

FORCE_SEND   = os.environ.get("FORCE_SEND", "false").lower() == "true"
FORCE_EVENT  = os.environ.get("FORCE_EVENT", "").strip()  # "anniv2025" | "newyear2026"

# ===== Helpers =====
def fail(msg: str):
    print(f"[CONFIG ERROR] {msg}")
    sys.exit(1)

def sanity_check():
    if not SENDER_EMAIL or "@" not in SENDER_EMAIL:
        fail("SENDER_EMAIL missing/invalid")
    if not RECEIVER_EMAILS:
        fail("No recipients. Set RECEIVER_EMAIL or RECEIVER_EMAILS")
    if not SMTP_PASSWORD:
        fail("Missing SMTP password (APP_PASSWORD or SMTP_PASSWORD)")
    # START_DATE quick check
    try:
        y, m, d = [int(x) for x in START_DATE.split("-")]
        _ = date(y, m, d)
    except Exception:
        fail("START_DATE must be YYYY-MM-DD (e.g., 2022-12-06)")

def parse_date(s: str) -> date:
    y, m, d = [int(x) for x in s.split("-")]
    return date(y, m, d)

def days_together(today: date) -> int:
    return (today - parse_date(START_DATE)).days + 1  # day 1 on START_DATE

# ===== Multi-event scheduler =====
WINDOW_SECS = 600  # ±10 minutes

def which_event(now_myt: datetime) -> Optional[str]:
    """Return the event key if within send window, else None."""
    tz = now_myt.tzinfo
    targets = [
        ("anniv2025",   datetime(2025, 12, 6, 5, 20, 0, tzinfo=tz)),
        ("newyear2026", datetime(2026,  1, 1, 0,  0, 0, tzinfo=tz)),
    ]
    for key, target in targets:
        if abs((now_myt - target).total_seconds()) <= WINDOW_SECS:
            return key
    return None

# ===== Bodies =====
def build_plain_anniv(today: date) -> str:
    d = days_together(today)
    return (
        f"{HER_NAME}，纪念日快乐！\n\n"
        f"今天是我们在一起的第 {d} 天 ❤️\n"
        f"给你的小惊喜：{PAGE_URL}\n"
        f"—— {today.strftime('%Y年%m月%d日')}"
    )

def build_html_anniv(today: date) -> str:
    d = days_together(today)
    date_str = today.strftime('%Y年%m月%d日')
    url = PAGE_URL
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#ffffff;">
    <div style="max-width:560px;margin:0 auto;padding:24px;
                font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;
                color:#111;font-size:16px;line-height:1.6;">
      <p style="margin:0 0 12px 0;">{HER_NAME}，纪念日快乐！</p>
      <p style="margin:0 0 18px 0;">今天是我们在一起的第 <strong>{d}</strong> 天 ❤️</p>
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 24px 0;">
        <tr>
          <td align="center">
            <!--[if mso]>
            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
              xmlns:w="urn:schemas-microsoft-com:office:word"
              href="{url}" style="height:44px;v-text-anchor:middle;width:240px;"
              arcsize="12%" strokecolor="#111111" fillcolor="#111111">
              <w:anchorlock/>
              <center style="color:#ffffff;font-family:Segoe UI,Arial,sans-serif;font-size:16px;font-weight:bold;">
                点我查看 🎁
              </center>
            </v:roundrect>
            <![endif]-->
            <!--[if !mso]><!-- -->
            <a href="{url}" target="_blank" rel="noopener noreferrer"
               style="background:#111111;color:#ffffff;display:inline-block;
                      padding:12px 22px;border-radius:8px;text-decoration:none;
                      font-weight:700;letter-spacing:.3px;">
              点我查看 🎁
            </a>
            <!--<![endif]-->
          </td>
        </tr>
      </table>
      <p style="margin:0 0 4px 0;font-size:14px;color:#555;">
        如果按钮无法打开，请点击或复制这个链接：<br>
        <a href="{url}" target="_blank" style="color:#1a73e8;">{url}</a>
      </p>
      <p style="margin:12px 0 0 0;">—— {date_str}</p>
    </div>
  </body>
</html>"""

def build_plain_newyear(today: date) -> str:
    d = days_together(today)
    return (
        f"{HER_NAME}，新年快乐！\n\n"
        f"我们的第 {d} 天，从新年的第一刻继续爱你 ❤️\n"
        f"给你的小惊喜：{PAGE_URL}\n"
        f"—— {today.strftime('%Y年%m月%d日')}"
    )

def build_html_newyear(today: date) -> str:
    d = days_together(today)
    date_str = today.strftime('%Y年%m月%d日')
    url = PAGE_URL
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#ffffff;">
    <div style="max-width:560px;margin:0 auto;padding:24px;
                font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;
                color:#111;font-size:16px;line-height:1.6;">
      <p style="margin:0 0 12px 0;">{HER_NAME}，新年快乐！🎆</p>
      <p style="margin:0 0 18px 0;">我们的第 <strong>{d}</strong> 天，从新年的第一刻继续爱你 ❤️</p>
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 24px 0;">
        <tr>
          <td align="center">
            <!--[if mso]>
            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
              xmlns:w="urn:schemas-microsoft-com:office:word"
              href="{url}" style="height:44px;v-text-anchor:middle;width:240px;"
              arcsize="12%" strokecolor="#111111" fillcolor="#111111">
              <w:anchorlock/>
              <center style="color:#ffffff;font-family:Segoe UI,Arial,sans-serif;font-size:16px;font-weight:bold;">
                点我看烟花 🎆
              </center>
            </v:roundrect>
            <![endif]-->
            <!--[if !mso]><!-- -->
            <a href="{url}" target="_blank" rel="noopener noreferrer"
               style="background:#111111;color:#ffffff;display:inline-block;
                      padding:12px 22px;border-radius:8px;text-decoration:none;
                      font-weight:700;letter-spacing:.3px;">
              点我看烟花 🎆
            </a>
            <!--<![endif]-->
          </td>
        </tr>
      </table>
      <p style="margin:0 0 4px 0;font-size:14px;color:#555;">
        如果按钮无法打开，请点击或复制这个链接：<br>
        <a href="{url}" target="_blank" style="color:#1a73e8;">{url}</a>
      </p>
      <p style="margin:12px 0 0 0;">—— {date_str}</p>
    </div>
  </body>
</html>"""

# ===== Send =====
def send_email(subject: str, body_plain: str, body_html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    msg.attach(MIMEText(body_plain, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as s:
        s.ehlo(); s.starttls(context=ctx); s.ehlo()
        try:
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
        except smtplib.SMTPAuthenticationError as e:
            print(f"[AUTH FAIL] {e.smtp_code}: {e.smtp_error}")
            raise
        s.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())

# ===== Main =====
if __name__ == "__main__":
    sanity_check()
    now = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))

    event = which_event(now)

    if not (FORCE_SEND or event):
        print("[SKIP] Outside target window. Set FORCE_SEND=true to test.")
        sys.exit(0)

    # If forcing locally, allow choosing a template
    if FORCE_SEND and not event:
        event = FORCE_EVENT or "anniv2025"

    today = now.date()

    if event == "newyear2026":
        subject = "🎆 新年快乐！给你的惊喜"
        body_plain = build_plain_newyear(today)
        body_html  = build_html_newyear(today)
    else:
        subject = "❤️ 纪念日的情书"
        body_plain = build_plain_anniv(today)
        body_html  = build_html_anniv(today)

    send_email(subject, body_plain, body_html)
    print(f"Email sent successfully. [event={event}]")
