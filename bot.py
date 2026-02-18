import os
import requests
import random
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

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
            candles = ""
            havdalah = ""
            for item in data["items"]:
                if item["category"] == "candles":
                    candles = item["title"].split(": ")[1]
                elif item["category"] == "havdalah":
                    havdalah = item["title"].split(": ")[1]
                elif item["category"] == "parashat":
                    parasha_name = item["hebrew"].replace("פרשת ", "")
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except Exception as e:
            print(f"Error: {e}")
    return parasha_name, results

def create_shabbat_image(parasha, times):
    # פתיחת הרקע
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        img = Image.open("image.png")
    else:
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 25)
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 25)
        font_header = ImageFont.truetype("Assistant-Bold.ttf", 18)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 18)
        font_dedication = ImageFont.truetype("Assistant-Bold.ttf", 20)
    except:
        font_logo = font_title = font_header = font_text = font_dedication = ImageFont.load_default()

    text_color = (40, 40, 40)
    highlight_color = (20, 50, 100) # כחול מלכותי
    bronze_color = (160, 110, 40)  # זהב-חום

    # 1. לוגו כחול בצד שמאל למעלה
    draw.text((20, 15), "2HalahotBeyom", font=font_logo, fill=highlight_color, anchor="lt")

    # 2. טבלה
    right_edge = W - 20 
    x_city = right_edge         
    x_candles = right_edge - 100  
    x_havdalah = right_edge - 180 

    current_y = 50
    full_title = f"שבת פרשת {parasha}"
    draw.text((x_city, current_y), full_title, font=font_title, fill=text_color, anchor="rt")

    current_y += 50
    draw.text((x_city, current_y), "עיר", font=font_header, fill=highlight_color, anchor="rt")
    draw.text((x_candles, current_y), "כניסה", font=font_header, fill=highlight_color, anchor="mt")
    draw.text((x_havdalah, current_y), "יציאה", font=font_header, fill=highlight_color, anchor="mt")
    
    current_y += 30
    draw.line((x_havdalah - 30, current_y, x_city, current_y), fill=text_color, width=3)

    current_y += 20
    for row in times:
        draw.text((x_city, current_y), row['city'], font=font_text, fill=text_color, anchor="rt")
        draw.text((x_candles, current_y), row['candles'], font=font_text, fill=text_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="mt")
        current_y += 30

    # 3. הקדשה
    current_y += 40
    draw.text((x_city, current_y), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=bronze_color, anchor="rt")

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
    payload = {'chat_id': CHANNEL_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(url, json=payload)

def main():
    now = datetime.datetime.now()
    weekday = now.weekday()
    current_hour_min = now.strftime("%H:%M")

    # ביום שישי ב-07:30 שולחים את התמונה
    if weekday == 4 and "07:28" < current_hour_min < "07:35":
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "שבת שלום ומבורך! 🕯️🍷")
    
    # ביום שישי ב-07:25 שולחים הלכות, וגם בכל יום חול אחר באותה שעה
    elif (weekday <= 4) and ("07:22" < current_hour_min < "07:27"):
        halachot = get_random_halachot()
        message = f"🌟 **הלכה יומית** 🌟\n\n1. {halachot[0]}\n\n2. {halachot[1]}\n\nיום מבורך! ✨"
        send_telegram_message(message)

if __name__ == "__main__":
    main()
