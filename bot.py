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
        # פונט השעות נשאר 52
        font_times = ImageFont.truetype("Assistant-Bold.ttf", 52) 
        # פונט ההקדשה הוגדל ב-20% (מ-28 ל-34)
        font_dedication = ImageFont.truetype("Shofar-Bold.ttf", 34) 
    except:
        font_times = font_dedication = ImageFont.load_default()

    black_color = (0, 0, 0)
    
    # --- הגדרות מיקומים ---
    x_candles = W * 0.68  # הוזז שמאלה (היה 0.72)
    x_havdalah = W * 0.55 # נשאר במקום המדויק (כי אמרת שזה טוב)
    
    start_y = H * 0.35    # הועלה קצת למעלה (היה 0.38)
    y_spacing = H * 0.08  

    # ציור הזמנים
    current_y = start_y
    for row in times:
        draw.text((x_candles, current_y), row['candles'], font=font_times, fill=black_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_times, fill=black_color, anchor="mt")
        current_y += y_spacing

    # ציור ההקדשה
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
    send_photo(path, "טסט על תבנית: כניסה שמאלה, הכל למעלה, הקדשה מוגדלת")

if __name__ == "__main__":
    main()
