import requests
import os
import random
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_ID")

def get_shabbat_times():
    cities = {
        "ירושלים": "281184",
        "תל אביב": "293397",
        "חיפה": "294801",
        "אילת": "295277"
    }
    
    message = "🕯️ **זמני כניסת ויציאת שבת:**\n"
    
    for city_name, city_id in cities.items():
        try:
            url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city_id}&m=50"
            res = requests.get(url).json()
            
            # שליפת זמנים מתוך ה-JSON של Hebcal
            items = res['items']
            candle_lighting = next(i['title'] for i in items if i['category'] == 'candles')
            havdalah = next(i['title'] for i in items if i['category'] == 'havdalah')
            
            # ניקוי הטקסט (לוקח רק את השעה)
            c_time = candle_lighting.split(": ")[1]
            h_time = havdalah.split(": ")[1]
            
            message += f"\n📍 **{city_name}:** {c_time} | {h_time}"
        except:
            continue
    return message

def job():
    if not os.path.exists("halachot.txt"):
        print("Missing halachot.txt")
        return

    # קריאת הלכות
    with open("halachot.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) >= 2:
        selected = random.sample(lines, 2)
        halacha_msg = f"📜 **2 הלכות יומיות:**\n\n1️⃣ {selected[0]}\n\n2️⃣ {selected[1]}"
        
        # אם היום יום שישי (יום 4 ב-Python כי 0 זה שני), נוסיף זמני שבת
        if datetime.now().weekday() == 4:
            shabbat_msg = get_shabbat_times()
            final_message = f"{halacha_msg}\n\n---\n{shabbat_msg}\n\nשבת שלום! ✡️"
        else:
            final_message = halacha_msg

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHANNEL, "text": final_message, "parse_mode": "Markdown"})
    else:
        print("Not enough lines")

if __name__ == "__main__":
    job()
