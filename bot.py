import os
import requests
import datetime
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def fix_hebrew(text):
    return get_display(arabic_reshaper.reshape(text))

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

    try: img = Image.open("shabbat_template.jpg")
    except: img = Image.new('RGB', (1200, 800), color='white')
    draw = ImageDraw.Draw(img)
    W, H = img.size

    try:
        font_times = ImageFont.truetype("Assistant-Bold.ttf", 57) 
        font_parashah = ImageFont.truetype("Shofar-Bold.ttf", 75)
    except: font_times = font_parashah = ImageFont.load_default()

    # הדפסת שם הפרשה במרכז למעלה
    draw.text((W / 2, H * 0.15), fix_hebrew(parashah_name), font=font_parashah, fill=(0,0,0), anchor="mm")

    current_y = H * 0.35
    for row in results:
        draw.text((W * 0.68, current_y), row['candles'], font=font_times, fill=(0,0,0), anchor="mt")
        draw.text((W * 0.53, current_y), row['havdalah'], font=font_times, fill=(0,0,0), anchor="mt")
        current_y += H * 0.08

    img.save("test_shabbat.jpg")

    # שליחה לטלגרם הפרטי
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    caption = f"טסט פרטי: שבת שלום ומבורך! 🕯️🍷\n*{parashah_name}*"
    with open("test_shabbat.jpg", 'rb') as f:
        requests.post(url, data={'chat_id': MY_TELEGRAM_ID, 'caption': caption}, files={'photo': f})

if __name__ == "__main__":
    test_shabbat()
