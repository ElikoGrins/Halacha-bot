import os
import requests
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות לבדיקה ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "269175916" # שולח אליך לפרטי לצורך הטסט

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
        except: pass
    return results

def create_shabbat_image(times):
    try:
        img = Image.open("shabbat_template.jpg")
    except Exception as e:
        print(f"שגיאה בטעינת התמונה: {e}")
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size

    try:
        # פונט שעות (גודל 52)
        font_times = ImageFont.truetype("Assistant-Bold.ttf", 52) 
        # פונט הקדשה ולוגו (גודל 34) - אותו פונט לשניהם
        font_dedication = ImageFont.truetype("Shofar-Bold.ttf", 34) 
    except:
        font_times = font_dedication = ImageFont.load_default()

    black_color = (0, 0, 0)
    
    # --- 1. ציור לוגו טלגרם בפינה השמאלית העליונה ---
    logo_x, logo_y = 30, 30
    icon_size = 34 # גודל האייקון תואם לגובה הטקסט
    draw_telegram_icon(draw, logo_x, logo_y, icon_size)
    # ציור הטקסט ליד האייקון באותו פונט של ההקדשה
    draw.text((logo_x + icon_size + 10, logo_y - 4), "2HalahotBeyom", font=font_dedication, fill=black_color, anchor="lt")

    # --- 2. הגדרות מיקומים לזמנים ---
    x_candles = W * 0.68  # נשאר ללא שינוי
    x_havdalah = W * 0.53 # הוזז מעט שמאלה (היה 0.55)
    
    start_y = H * 0.35    
    y_spacing = H * 0.08  

    # --- 3. ציור הזמנים ---
    current_y = start_y
    for row in times:
        draw.text((x_candles, current_y), row['candles'], font=font_times, fill=black_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_times, fill=black_color, anchor="mt")
        current_y += y_spacing

    # --- 4. ציור ההקדשה (באותו פונט של הלוגו) ---
    draw.text((W - 40, H - 40), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=black_color, anchor="rd")

    final_path = "shabbat_test.jpg"
    img.save(final_path)
    return final_path

def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def main():
    times = get_shabbat_times()
    path = create_shabbat_image(times)
    send_photo(path, "טסט: יציאה שמאלה, נוסף לוגו טלגרם למעלה")

if __name__ == "__main__":
    main()
