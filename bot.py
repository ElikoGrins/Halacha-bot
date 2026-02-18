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

# --- הגדרות ערוץ (כרגע במצב בדיקה על ה-ID שלך) ---
CHANNEL_ID = "269175916" 
# כשתסיים לבדוק, תחזיר את השורה הזו להערה ותפעיל את השורה למטה:
# CHANNEL_ID = os.environ.get("CHANNEL_ID")

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
    print("Creating layout...")
    
    # 1. יצירת קנבס חדש ונקי (בגודל סטורי - 1080x1350)
    # צבע הרקע הוא אפור בהיר מאוד שיתאים לקיר בתמונה שלך
    canvas_width = 1080
    canvas_height = 1350
    final_img = Image.new('RGB', (canvas_width, canvas_height), color=(230, 230, 230))
    
    # 2. טעינת תמונת הרקע שלך
    bg_loaded = False
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        original_img = Image.open("Shabbat_bg.jpg.JPG")
        bg_loaded = True
    elif os.path.exists("image.png"):
        original_img = Image.open("image.png")
        bg_loaded = True
    
    # 3. הדבקת התמונה למטה
    if bg_loaded:
        # התאמת רוחב התמונה לרוחב הקנבס (1080)
        ratio = canvas_width / original_img.width
        new_height = int(original_img.height * ratio)
        resized_bg = original_img.resize((canvas_width, new_height))
        
        # הדבקה בחלק התחתון של הקנבס
        final_img.paste(resized_bg, (0, canvas_height - new_height))
    
    draw = ImageDraw.Draw(final_img)
    
    # 4. טעינת פונטים
    try:
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 90)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 55) # הקטנתי קצת שייכנס יפה
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 45)
    except:
        font_title = font_text = font_logo = ImageFont.load_default()

    text_color = (40, 40, 40) # אפור כהה
    gold_color = (160, 120, 10) # זהב כהה

    # לוגו (למעלה בצד)
    draw.text((40, 40), "2HalahotBeyom", font=font_logo, fill=text_color)

    # כותרת ראשית (למעלה במרכז - בשטח הריק)
    title = fix_text(f"שבת פרשת {parasha}")
    bbox = draw.textbbox((0, 0), title, font=font_title)
    w = bbox[2] - bbox[0]
    # מיקום קבוע בגובה 150 פיקסלים
    draw.text(((canvas_width - w) / 2, 150), title, font=font_title, fill=text_color)

    # כותרות טבלה
    header = fix_text("   עיר        כניסה       יציאה   ")
    bbox_h = draw.textbbox((0, 0), header, font=font_text)
    w_h = bbox_h[2] - bbox_h[0]
    draw.text(((canvas_width - w_h) / 2, 350), header, font=font_text, fill=gold_color)
    
    draw.line((150, 430, canvas_width - 150, 430), fill=text_color, width=3)

    # נתונים
    y = 480
    for row in times:
        city = fix_text(row['city'])
        # עיר בימין
        draw.text((canvas_width - 250, y), city, font=font_text, fill=text_color, anchor="rs")
        # כניסה באמצע
        draw.text((canvas_width / 2, y), row['candles'], font=font_text, fill=text_color, anchor="ms")
        # יציאה בשמאל
        draw.text((250, y), row['havdalah'], font=font_text, fill=text_color, anchor="ls")
        y += 100

    final_img.save("shabbat_final.jpg")
    return "shabbat_final.jpg"

def send_photo(image_path, caption):
    print(f"Sending photo to {CHANNEL_ID}...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        resp = requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})
    print(f"Telegram response: {resp.text}")

def main():
    print("Starting bot (Visual Fix)...")
    
    # מצב בדיקה פעיל
    if True: 
        print("Simulating Friday...")
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "בדיקת עיצוב סופית - תיקון פרופורציות")

if __name__ == "__main__":
    main()
