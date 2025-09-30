# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, date
from zoneinfo import ZoneInfo
import ssl
import sys

SENDER_EMAIL   = os.environ.get("SENDER_EMAIL", "").strip()
APP_PASSWORD   = os.environ.get("APP_PASSWORD", "").strip()
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "").strip()
START_DATE     = os.environ.get("START_DATE", "2022-12-06").strip()
HER_NAME       = os.environ.get("HER_NAME", "宝贝").strip()

def fail(msg: str):
    print(f"[CONFIG ERROR] {msg}")
    sys.exit(1)

def sanity_check():
    if not SENDER_EMAIL or "@" not in SENDER_EMAIL:
        fail("SENDER_EMAIL 缺失或格式不对")
    if not RECEIVER_EMAIL or "@" not in RECEIVER_EMAIL:
        fail("RECEIVER_EMAIL 缺失或格式不对")
    if not APP_PASSWORD:
        fail("APP_PASSWORD 缺失（必须是 Gmail 应用专用密码，而不是登录密码）")
    if len(APP_PASSWORD.replace(" ", "")) != 16:
        print("[WARN] APP_PASSWORD 长度似乎不是 16，可能不是应用专用密码或有空格")
    try:
        y, m, d = [int(x) for x in START_DATE.split("-")]
        _ = date(y, m, d)
    except Exception:
        fail("START_DATE 必须是 YYYY-MM-DD，例如 2022-12-06")

def parse_date(s: str) -> date:
    y, m, d = [int(x) for x in s.split("-")]
    return date(y, m, d)

def days_together(today: date) -> int:
    return (today - parse_date(START_DATE)).days + 1

def build_message(today: date) -> str:
    d = days_together(today)
    lines = [
        f"{HER_NAME}，纪念日快乐！",
        "",
        f"今天是我们在一起的第 {d} 天 ❤️",
        "谢谢你一直在我身边，未来也请多多关照～",
        f"—— {today.strftime('%Y年%m月%d日')}",
    ]
    return "\n".join(lines)

def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        try:
            server.login(SENDER_EMAIL, APP_PASSWORD)
        except smtplib.SMTPAuthenticationError as e:
            code, resp = e.smtp_code, e.smtp_error
            print(f"[AUTH FAIL] SMTPAuthenticationError {code}: {resp}")
            print("排查：1) 确认已开两步验证并使用【应用专用密码】；"
                  "2) SENDER_EMAIL 必须与生成该密码的 Gmail 相同；"
                  "3) 重新生成 App Password，更新 Secrets 再试。")
            raise
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())

if __name__ == "__main__":
    sanity_check()
    today = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()
    subject = "❤️ 纪念日的情书"
    body = build_message(today)
    send_email(subject, body)
    print("Email sent successfully.")
