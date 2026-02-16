import requests
import os
import random

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_ID")

def job():
    # בדיקה אם הקובץ קיים
    if not os.path.exists("halachot.txt"):
        print("קובץ halachot.txt לא נמצא!")
        return

    with open("halachot.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) >= 2:
        # בוחר 2 הלכות אקראיות
        selected = random.sample(lines, 2)
        message = f"📜 **הלכה יומית**\n\n1️⃣ {selected[0]}\n\n2️⃣ {selected[1]}"
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHANNEL, "text": message})
    else:
        print("אין מספיק הלכות בקובץ")

if __name__ == "__main__":
    job()
