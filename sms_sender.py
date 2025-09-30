# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from zoneinfo import ZoneInfo  # Python 3.9+
from twilio.rest import Client

# 从环境变量读取配置（全部都从 GitHub Secrets 注入）
ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
FROM_NUMBER = os.environ["TWILIO_FROM_NUMBER"]   # 形如 +1XXXXXXXX
TO_NUMBER   = os.environ["TO_NUMBER"]            # 形如 +60XXXXXXXX
START_DATE  = os.environ.get("START_DATE", "2022-08-01")
HER_NAME    = os.environ.get("HER_NAME", "宝贝")
LINK        = os.environ["LINK"]                 # 想发给她的链接
DRY_RUN     = os.environ.get("DRY_RUN", "false").lower() == "true"  # 测试不真正发

def parse_date(s: str) -> date:
    y, m, d = [int(x) for x in s.split("-")]
    return date(y, m, d)

def days_together(today: date) -> int:
    # 第一天算第1天
    return (today - parse_date(START_DATE)).days + 1

def build_message(today: date) -> str:
    d = days_together(today)
    return (
        f"{HER_NAME}，纪念日快乐！今天是我们在一起的第 {d} 天 ❤️\n"
        f"给你的小惊喜 👉 {LINK}\n"
        f"—— {today.strftime('%Y年%m月%d日')}"
    )

def send_sms(body: str):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    msg = client.messages.create(
        body=body,
        from_=FROM_NUMBER,
        to=TO_NUMBER
    )
    print("Sent SID:", msg.sid)

def main():
    today_myt = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()
    body = build_message(today_myt)
    if DRY_RUN:
        print("[DRY RUN] 将要发送的短信：\n", body)
        return
    send_sms(body)

if __name__ == "__main__":
    main()
