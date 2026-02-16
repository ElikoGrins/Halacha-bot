import requests
import time
import schedule
import os

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL,
        "text": text
    }
    requests.post(url, data=data)

def job():
    with open("halachot.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) >= 2:
        message = "📖 2 הלכות יומיות\n\n" + lines[0] + "\n" + lines[1]
        send_message(message)

        with open("halachot.txt", "w", encoding="utf-8") as f:
            f.writelines(lines[2:])

schedule.every().day.at("07:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
