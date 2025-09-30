# -*- coding: utf-8 -*-
import smtplib, os
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, date
from zoneinfo import ZoneInfo

# ====== 配置从 GitHub Secrets 读取 ======
SENDER_EMAIL   = os.environ["SENDER_EMAIL"]    # 你的 Gmail
APP_PASSWORD   = os.environ["APP_PASSWORD"]    # 应用专用密码
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]  # 她的邮箱
START_DATE     = os.environ.get("START_DATE", "2022-08-01")
HER_NAME       = os.environ.get("HER_NAME", "宝贝")

def parse_date(s: str) -> date:
    y, m, d = [int(x) for x in s.split("-")]
    return date(y, m, d)

def days_together(today: date) -> int:
    return (today - parse_date(START_DATE)).days + 1

def build_message(today: date) -> str:
    d = days_together(today)
    return (
        f"{HER_NAME}，纪念日快乐！\n\n"
        f"今天是我们在一起的第 {d} 天 ❤️\n"
        f"谢谢你一直在我身边，未来也请多多关照～\n"
        f"—— {today.strftime('%Y年%m月%d日')}"
    )

def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())

if __name__ == "__main__":
    today = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()
    subject = "❤️ 纪念日的情书"
    body = build_message(today)
    send_email(subject, body)
    print("Email sent successfully.")
