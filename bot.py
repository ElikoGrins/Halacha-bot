import os
import requests
import random
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות סופיות ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID") # חוזר לערוץ הכללי

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"}
]

def get_shabbat_times():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    date_str = friday.strftime("%Y-%m-%d")
    results = []
    parasha_name = ""
    for city in CITIES:
        url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city['geonameid']}&date={date_str}&M=on"
        try:
            response = requests.get(url)
            data = response.json()
            candles, havdalah = "", ""
            for item in data["items"]:
                if item["category"] == "candles":
                    candles = item["title"].split(": ")[1]
                elif item["category"] == "havdalah":
                    havdalah = item["title"].split(": ")[1]
                elif item["category"] == "parashat":
                    parasha_name = item["hebrew"].replace("פרשת ", "")
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except: pass
    return parasha_name, results

def create_shabbat_image(parasha, times):
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    else:
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    font_shofar = "Shofar-Bold.ttf"
    font_assistant = "Assistant-Bold.ttf"
    
    try:
        font_logo = ImageFont.truetype(font_shofar, 18)
        font_main_title = ImageFont.truetype(font_assistant, 26)
        font_parasha = ImageFont.truetype(font_shofar, 24)
        font_header = ImageFont.truetype(font_shofar, 16) 
        font_text = ImageFont.truetype(font_shofar, 16)   
        font_dedication = ImageFont.truetype(font_shofar, 20)
    except:
        font_logo = font_main_title = font_parasha = font_header = font_text = font_dedication = ImageFont.load_default()

    black_color = (0, 0, 0)
    text_color = (40, 40, 40)
    highlight_color = (20, 50, 100) # כחול מלכותי
    gold_deep = (184, 134, 11)      # זהב כהה (Dark Goldenrod)

    # 1. לוגו - פינה שמאלית עליונה
    draw.text((15, 10), "2HalahotBeyom", font=font_logo, fill=highlight_color, anchor="lt")

    # 2. כותרות - ימין
    right_edge = W - 30 
    top_y = 25
    title_text = "זמני כניסת ויציאת שבת"
    draw.text((right_edge, top_y), title_text, font=font_main_title, fill=black_color, anchor="rt")
    
    title_bbox = draw.textbbox((right_edge, top_y), title_text, font=font_main_title, anchor="rt")
    title_center_x = (title_bbox[0] + title_bbox[2]) / 2
    
    current_y = top_y + 35
    draw.text((title_center_x, current_y), f"פרשת {parasha}", font=font_parasha, fill=gold_deep, anchor="mt")

    # 3. טבלה
    x_city, x_candles, x_havdalah = right_edge, right_edge - 90, right_edge - 170 

    current_y += 45 
    draw.text((x_candles, current_y), "כניסה", font=font_header, fill=highlight_color, anchor="mt")
    draw.text((x_havdalah, current_y), "יציאה", font=font_header, fill=highlight_color, anchor="mt")
    
    current_y += 22 
    draw.line((x_havdalah - 35, current_y, x_city, current_y), fill=text_color, width=2)

    current_y += 10 
    for row in times:
        draw.text((x_city, current_y), row['city'], font=font_text, fill=text_color, anchor="rt")
        draw.text((x_candles, current_y), row['candles'], font=font_text, fill=text_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="mt")
        current_y += 26 

    # 4. הקדשה - ירדה עוד קצת למטה
    current_y += 40 
    draw.text((right_edge, current_y), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=highlight_color, anchor="rt")

    img.save("shabbat_final.jpg")
    return "shabbat_final.jpg"

def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def get_random_halachot():
    with open('halachot.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return random.sample(lines, 2)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text, 'parse_mode': 'Markdown'})

def main():
    now = datetime.datetime.now()
    weekday = now.weekday()
    current_time = now.strftime("%H:%M")

    # ריצה ב-07:30 ביום שישי (תמונה)
    if weekday == 4 and "07:28" < current_time < "07:35":
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "שבת שלום ומבורך! 🕯️🍷")
    
    # ריצה ב-07:25 (הלכות) - בימי חול ושישי
    elif weekday <= 4 and "07:22" < current_time < "07:27":
        h = get_random_halachot()
        msg = f"🌟 **הלכה יומית** 🌟\n\n1. {h[0]}\n\n2. {h[1]}\n\nיום מבורך! ✨"
        send_telegram_message(msg)

if __name__ == "__main__":
    main()
