# -*- coding: utf-8 -*-
"""
email_sender.py
- 每年 12/06 05:20（Asia/Kuala_Lumpur）自动发送纪念日邮件
- 计算“在一起第 N 天”，并附上你的 GitHub Pages 链接
- 支持一次发给多人（用 RECEIVER_EMAILS，逗号分隔）
- 可用 FORCE_SEND=true 强制发送（便于手动测试）

环境变量（GitHub Secrets）：
- SENDER_EMAIL      必填：你的 Gmail 地址
- APP_PASSWORD      必填：Gmail 应用专用密码（16位）
- RECEIVER_EMAIL    二选一：单个收件人
- RECEIVER_EMAILS   二选一：多个收件人，逗号分隔
- START_DATE        选填：YYYY-MM-DD，默认 2022-12-06
- HER_NAME          选填：称呼，默认 Baby
- PAGE_URL          选填：页面链接，默认 https://jowenthebui.github.io/letterstomylove/
- FORCE_SEND        选填：true/false（默认 false），手动触发时强制发送

（可选自定义SMTP，若你改用SendGrid等）
- SMTP_SERVER       选填：默认 smtp.gmail.com
- SMTP_PORT         选填：默认 587
- SMTP_USERNAME     选填：默认 SENDER_EMAIL（SendGrid用 'apikey'）
- SMTP_PASSWORD     选填：默认 APP_PASSWORD（SendGrid用 API Key）
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, date
from zoneinfo import ZoneInfo
import sys


# ===== 读取配置 =====
SENDER_EMAIL   = os.environ.get("SENDER_EMAIL", "").strip()
APP_PASSWORD   = os.environ.get("APP_PASSWORD", "").strip()
# 收件人优先用 RECEIVER_EMAILS（多人）
_raw_multi = os.environ.get("RECEIVER_EMAILS", "")
RECEIVER_EMAILS = [e.strip() for e in _raw_multi.split(",") if e.strip()]
if not RECEIVER_EMAILS:
    # 回退到单个
    single = os.environ.get("RECEIVER_EMAIL", "").strip()
    if single:
        RECEIVER_EMAILS = [single]

START_DATE = os.environ.get("START_DATE", "2022-12-06").strip()
HER_NAME   = os.environ.get("HER_NAME", "Baby").strip()
PAGE_URL   = os.environ.get("PAGE_URL", "https://jowenthebui.github.io/letterstomylove/").strip()

# 可选：自定义SMTP（如 SendGrid）
SMTP_SERVER   = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", SENDER_EMAIL).strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", APP_PASSWORD).strip()

FORCE_SEND = os.environ.get("FORCE_SEND", "false").lower() == "true"


# ===== 基础函数 =====
def fail(msg: str):
    print(f"[CONFIG ERROR] {msg}")
    sys.exit(1)

def sanity_check():
    if not SENDER_EMAIL or "@" not in SENDER_EMAIL:
        fail("SENDER_EMAIL 缺失或格式不对")
    if not RECEIVER_EMAILS:
        fail("没有收件人。请设置 RECEIVER_EMAIL 或 RECEIVER_EMAILS")
    if not SMTP_PASSWORD:
        fail("缺少 SMTP 密码（APP_PASSWORD 或 SMTP_PASSWORD）")
    # 简单校验 App Password 长度（Gmail）
    if SMTP_SERVER == "smtp.gmail.com" and len(APP_PASSWORD.replace(" ", "")) != 16:
        print("[WARN] APP_PASSWORD 长度不是 16，确认是否为 Gmail 应用专用密码。")
    # START_DATE 格式校验
    try:
        y, m, d = [int(x) for x in START_DATE.split("-")]
        _ = date(y, m, d)
    except Exception:
        fail("START_DATE 必须是 YYYY-MM-DD（例如 2022-12-06）")

def parse_date(s: str) -> date:
    y, m, d = [int(x) for x in s.split("-")]
    return date(y, m, d)

def days_together(today: date) -> int:
    # 第一天计为 1
    return (today - parse_date(START_DATE)).days + 1

def build_message(today: date) -> str:
    d = days_together(today)
    lines = [
        f"{HER_NAME}，纪念日快乐！",
        "",
        f"今天是我们在一起的第 {d} 天 ❤️",
        f"给你的小惊喜 👉 {PAGE_URL}",
        f"—— {today.strftime('%Y年%m月%d日')}",
    ]
    return "\n".join(lines)

def should_send(now_myt: datetime) -> bool:
    """
    只在每年 12/06 05:20（马来西亚时间）发送。
    允许 ±10 分钟窗口，避免平台调度轻微延迟。
    """
    target = now_myt.replace(year=now_myt.year, month=12, day=6, hour=5, minute=20, second=0, microsecond=0)
    return abs((now_myt - target).total_seconds()) <= 600


# ===== 发送邮件 =====
def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.ehlo()
        try:
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
        except smtplib.SMTPAuthenticationError as e:
            print(f"[AUTH FAIL] {e.smtp_code}: {e.smtp_error}")
            print("检查：1) 若用 Gmail，请确保使用【应用专用密码】；"
                  "2) SENDER_EMAIL 与生成该密码的账号一致；"
                  "3) 如仍失败，可改用 SendGrid，并设置 SMTP_* 环境变量。")
            raise
        s.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())


# ===== 主流程 =====
if __name__ == "__main__":
    sanity_check()
    now = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
    if not (FORCE_SEND or should_send(now)):
        print("[SKIP] 非目标时间窗口，不发送。若要手动测试真实发送，请设置 FORCE_SEND=true。")
        sys.exit(0)

    today = now.date()
    subject = "❤️ 纪念日的情书"
    body = build_message(today)
    send_email(subject, body)
    print("Email sent successfully.")
