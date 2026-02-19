import os
import requests
import random
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות שרת (Production) ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID") # שולח לערוץ הכללי המוגדר ב-Secrets

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"}
]

# פונקציה לציור אייקון טלגרם
def draw_telegram_icon(draw, x, y, size):
    # עיגול כחול
    bg_color = (36, 161, 222)
    draw.ellipse([x, y, x + size, y + size], fill=bg_color)
    # מטוס נייר לבן
    p = [(x+size*0.25, y+size*0.5), (x+size*0.75, y+size*0.3), (x+size*0.6, y+size*0.7), (x+size*0.5, y+size*0.55)]
    draw.polygon(p, fill="white")

def get_shabbat_times():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    date_str = friday.strftime("%Y-%m-%d")
    results = []
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
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except Exception as e:
            print(f"Error fetching times for {city['name']}: {e}")
    return results

def create_shabbat_image(times):
    # 1. טעינת התבנית המוכנה
    try:
        img = Image.open("shabbat_template.jpg")
    except Exception as e:
        print(f"שגיאה בטעינת התמונה: {e}")
        # במקרה חירום בלבד: תמונה ריקה
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size

    # 2. הגדרת פונטים (בגדלים המדויקים)
    try:
        font_times = ImageFont.truetype("Assistant-Bold.ttf", 57) 
        font_dedication = ImageFont.truetype("Shofar-Bold.ttf", 37) 
    except:
        font_times = font_dedication = ImageFont.load_default()

    black_color = (0, 0, 0)
    
    # --- 3. ציור לוגו טלגרם בפינה השמאלית העליונה ---
    logo_x, logo_y = 30, 30
    icon_size = 37 
    draw_telegram_icon(draw, logo_x, logo_y, icon_size)
    draw.text((logo_x + icon_size + 10, logo_y - 4), "2HalahotBeyom", font=font_dedication, fill=black_color, anchor="lt")

    # --- 4. הגדרות מיקומים לזמנים ---
    x_candles = W * 0.68  
    x_havdalah = W * 0.53 
    start_y = H * 0.35    
    y_spacing = H * 0.08  

    # --- 5. ציור הזמנים על התבנית ---
    current_y = start_y
    for row in times:
        draw.text((x_candles, current_y), row['candles'], font=font_times, fill=black_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_times, fill=black_color, anchor="mt")
        current_y += y_spacing

    # --- 6. ציור ההקדשה ---
    draw.text((W - 40, H - 40), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=black_color, anchor="rd")

    final_path = "shabbat_final.jpg"
    img.save(final_path)
    return final_path

def get_random_halachot():
    with open('halachot.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return random.sample(lines, 2)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text, 'parse_mode': 'Markdown'})

def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def main():
    # בדיקת היום בשבוע (0=שני, ..., 4=שישי)
    weekday = datetime.datetime.now().weekday()

    if weekday == 4:
        # יום שישי - יצירת תמונה ושליחתה
        print("Today is Friday. Generating and sending Shabbat image...")
        times = get_shabbat_times()
        path = create_shabbat_image(times)
        send_photo(path, "שבת שלום ומבורך! 🕯️🍷")
        print("Shabbat image sent successfully.")
    else:
        # ימים אחרים - שליחת הלכות
        print("Sending daily halachot...")
        h = get_random_halachot()
        msg = f"🌟 **הלכה יומית** 🌟\n\n1. {h[0]}\n\n2. {h[1]}\n\nיום מבורך! ✨"
        send_telegram_message(msg)
        print("Halachot sent successfully.")

if __name__ == "__main__":
    main()
