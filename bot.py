import os
import requests
import datetime
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.environ.get("BOT_TOKEN")

MY_TELEGRAM_ID = "269175916"

CITIES = [{"name": "ירושלים", "geonameid": "281184"}, {"name": "תל אביב", "geonameid": "293397"}, 
          {"name": "חיפה", "geonameid": "294801"}, {"name": "באר שבע", "geonameid": "295530"}]

def test_shabbat():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    date_str = friday.strftime("%Y-%m-%d")
    results, parashah_name = [], ""

    for city in CITIES:
        url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city['geonameid']}&date={date_str}&M=on"
        try:
            data = requests.get(url).json()
            candles = havdalah = ""
            for item in data["items"]:
                if item["category"] == "parashat" and not parashah_name:
                    parashah_name = item.get("hebrew", item.get("title"))
                elif item["category"] == "candles":
                    candles = item["title"].split(": ")[1]
                elif item["category"] == "havdalah":
                    havdalah = item["title"].split(": ")[1]
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except: pass
    
    if not parashah_name: parashah_name = "שבת שלום ומבורך"

    # מציאת התמונה שלך
    img_path = None
    possible_names = ["shabbat_template.jpg", "shabbat_template.jpeg", "shabbat_template.JPG", 
                      "Shabbat_template.jpg", "shabbat_template.png"]
    
    for name in possible_names:
        if os.path.exists(name):
            img_path = name
            break
            
    if img_path:
        img = Image.open(img_path)
    else:
        print("לא מצאתי את התמונה! מייצר רקע לבן זמני.")
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size

    # הגדרת צבע חום יוקרתי
    brown_color = (101, 67, 33)
    black_color = (0, 0, 0)

    try:
        font_times = ImageFont.truetype("Assistant-Bold.ttf", 55) 
        # הגדלתי את הפונט ב-10% (מ-95 ל-105)
        font_parashah = ImageFont.truetype("Shofar-Bold.ttf", 105)
    except: font_times = font_parashah = ImageFont.load_default()

    # === מיקום ועיצוב פרשה ===
    # הזזתי עוד ימינה (0.64) ועוד למעלה (0.195) ושיניתי לצבע חום
    draw.text((W * 0.64, H * 0.195), parashah_name, font=font_parashah, fill=brown_color, anchor="mm")

    # === מיקום וריווח טבלה ===
    # העליתי את כל הטבלה עוד למעלה (0.345)
    current_y = H * 0.345
    # הגדלתי טיפה את הרווח בין השורות (0.072)
    y_spacing = H * 0.072
    
    for row in results:
        draw.text((W * 0.68, current_y), row['candles'], font=font_times, fill=black_color, anchor="mt")
        draw.text((W * 0.53, current_y), row['havdalah'], font=font_times, fill=black_color, anchor="mt")
        current_y += y_spacing

    img.save("test_shabbat.jpg")

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    caption = f"טסט פרטי: שבת שלום ומבורך! 🕯️🍷\n*{parashah_name}*"
    with open("test_shabbat.jpg", 'rb') as f:
        requests.post(url, data={'chat_id': MY_TELEGRAM_ID, 'caption': caption}, files={'photo': f})

if __name__ == "__main__":
    test_shabbat()
