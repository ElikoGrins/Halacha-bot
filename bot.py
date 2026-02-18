import os
import requests
import random
import datetime
import json
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# --- הגדרות ---
TOKEN = os.environ.get("BOT_TOKEN")

# --- שים לב: השארתי כאן את ה-ID שלך לבדיקה אחרונה ---
# אחרי שתראה שהתמונה מגיעה יפה, תחזיר את השורה הזו להיות:
# CHANNEL_ID = os.environ.get("CHANNEL_ID")
CHANNEL_ID = "269175916" 

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"},
    {"name": "אילת", "geonameid": "295277"}
]

# --- פונקציות עזר ---
def fix_text(text):
    if not text: return ""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def get_shabbat_times():
    print("Fetching Shabbat times...")
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
                    parasha_name = item["hebrew"]
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except Exception as e:
            print(f"Error fetching {city['name']}: {e}")
            
    return parasha_name, results

def create_shabbat_image(parasha, times):
    print("Looking for background image...")
    
    # --- התיקון הגדול כאן: השם המדויק של הקובץ שלך ---
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        print("Found Shabbat_bg.jpg.JPG")
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        print("Found image.png")
        img = Image.open("image.png")
    else:
        print("Background image NOT found! Using white background.")
        img = Image.new('RGB', (1080, 1350), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # טעינת פונטים
    try:
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 90)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 60)
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 45)
    except:
        print("Font not found, using default.")
        font_title = font_text = font_logo = ImageFont.load_default()

    text_color = (50, 50, 50)
    gold_color = (184, 134, 11)

    # לוגו
    draw.text((30, 30), "2HalahotBeyom", font=font_logo, fill=text_color)

    # כותרת
    title = fix_text(f"שבת פרשת {parasha}")
    bbox = draw.textbbox((0, 0), title, font=font_title)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, 180), title, font=font_title, fill=text_color)

    # כותרות טבלה
    header = fix_text("   עיר        כניסה       יציאה   ")
    bbox_h = draw.textbbox((0, 0), header, font=font_text)
    w_h = bbox_h[2] - bbox_h[0]
    draw.text(((W - w_h) / 2, 400), header, font=font_text, fill=gold_color)
    
    draw.line((100, 480, W - 100, 480), fill=text_color, width=3)

    # נתונים
    y = 530
    for row in times:
        city = fix_text(row['city'])
        draw.text((W - 200, y), city, font=font_text, fill=text_color, anchor="rs")
        draw.text((W / 2, y), row['candles'], font=font_text, fill=text_color, anchor="ms")
        draw.text((200, y), row['havdalah'], font=font_text, fill=text_color, anchor="ls")
        y += 110

    img.save("final_shabbat.jpg")
    return "final_shabbat.jpg"

def send_photo(image_path, caption):
    print(f"Sending photo to {CHANNEL_ID}...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        resp = requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})
    print(f"Telegram response: {resp.text}")

def main():
    # --- מצב בדיקה מופעל ---
    print("Starting bot in TEST mode...")
    
    # מכריחים את הבוט לחשוב שיום שישי
    if True: 
        print("Simulating Friday...")
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "בדיקת עיצוב שבת סופית")

if __name__ == "__main__":
    main()
