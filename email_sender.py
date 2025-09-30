# -*- coding: utf-8 -*-
"""
email_sender.py — HTML version with SURPRISE button
- Sends an HTML email (with plain-text fallback) so "SURPRISE" is clickable
- Time gate: only sends at 12/06 05:20 Asia/Kuala_Lumpur unless FORCE_SEND=true
- Supports multiple recipients via RECEIVER_EMAILS (comma-separated)

Required secrets (env):
  SENDER_EMAIL, APP_PASSWORD, (RECEIVER_EMAIL or RECEIVER_EMAILS),
  START_DATE, HER_NAME, PAGE_URL
Optional:
  FORCE_SEND ("true"/"false"), SMTP_SERVER/PORT/USERNAME/PASSWORD for custom SMTP
"""
import os, smtplib, ssl, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime, date
from zoneinfo import ZoneInfo

# ===== Config =====
SENDER_EMAIL   = os.environ.get("SENDER_EMAIL", "").strip()
APP_PASSWORD   = os.environ.get("APP_PASSWORD", "").strip()
_raw_multi = os.environ.get("RECEIVER_EMAILS", "")
RECEIVER_EMAILS = [e.strip() for e in _raw_multi.split(",") if e.strip()]
if not RECEIVER_EMAILS:
    one = os.environ.get("RECEIVER_EMAIL", "").strip()
    if one: RECEIVER_EMAILS = [one]

START_DATE = os.environ.get("START_DATE", "2022-12-06").strip()
HER_NAME   = os.environ.get("HER_NAME", "Baby").strip()
PAGE_URL   = os.environ.get("PAGE_URL", "https://wenjoo.github.io/letterstomylove/").strip()

SMTP_SERVER   = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", SENDER_EMAIL).strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", APP_PASSWORD).strip()

FORCE_SEND = os.environ.get("FORCE_SEND", "false").lower() == "true"

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
    # quick START_DATE check
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

def should_send(now_myt: datetime) -> bool:
    target = now_myt.replace(year=now_myt.year, month=12, day=6, hour=5, minute=20, second=0, microsecond=0)
    return abs((now_myt - target).total_seconds()) <= 600  # ±10 min window

# ===== Bodies =====
def build_plain(today: date) -> str:
    d = days_together(today)
    return (
        f"{HER_NAME}，纪念日快乐！\n\n"
        f"今天是我们在一起的第 {d} 天 ❤️\n"
        f"给你的小惊喜：{PAGE_URL}\n"
        f"—— {today.strftime('%Y年%m月%d日')}"
    )

def build_html(today: date) -> str:
    d = days_together(today)
    date_str = today.strftime('%Y年%m月%d日')
    # Simple, bulletproof inline styles for email
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#ffffff;">
    <div style="max-width:560px;margin:0 auto;padding:24px;
                font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;
                color:#111;font-size:16px;line-height:1.6;">
      <p style="margin:0 0 12px 0;">{HER_NAME}，纪念日快乐！</p>
      <p style="margin:0 0 18px 0;">今天是我们在一起的第 <strong>{d}</strong> 天 ❤️</p>
      <p style="margin:0 0 24px 0;">
        <a href="{PAGE_URL}" target="_blank"
           style="display:inline-block;background:#111;color:#fff;text-decoration:none;
                  padding:12px 20px;border-radius:8px;font-weight:700;letter-spacing:.5px;">
          SURPRISE
        </a>
      </p>
      <p style="margin:0 0 4px 0;">—— {date_str}</p>
    </div>
  </body>
</html>"""

# ===== Send =====
def send_email(subject: str, body_plain: str, body_html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    # attach plain + html (clients pick best)
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
    if not (FORCE_SEND or should_send(now)):
        print("[SKIP] Outside target window. Set FORCE_SEND=true to test.")
        sys.exit(0)

    today = now.date()
    subject = "❤️ 纪念日的情书"
    send_email(subject, build_plain(today), build_html(today))
    print("Email sent successfully.")
