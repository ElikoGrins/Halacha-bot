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
# מצב בדיקה - שולח אליך לפרטי
CHANNEL_ID = "269175916" 

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"}
]

def fix_text(text):
    if not text: return ""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def get_shabbat_times():
    print("Fetching times...")
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
            print(f"Error {city['name']}: {e}")
    return parasha_name, results

def create_shabbat_image(parasha, times):
    print("Creating layout...")
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        img = Image.open("image.png")
    else:
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # פונטים קטנים יותר
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 40)
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 45)
        font_header = ImageFont.truetype("Assistant-Bold.ttf", 35)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 30)
    except:
        font_logo = font_title = font_header = font_text = ImageFont.load_default()

    text_color = (40, 40, 40)
    gold_color = (180, 130, 20)

    # --- לוגו: נמוך יותר ורחוק מהנר ---
    logo_x = 70
    logo_y = 100
    draw.text((logo_x, logo_y), "2HalahotBeyom", font=font_logo, fill=text_color, anchor="la")

    # --- כותרת ראשית: נמוכה יותר ---
    title = fix_text(f"שבת פרשת {parasha}")
    title_x = W * 0.75
    title_y = 250
    draw.text((title_x, title_y), title, font=font_title, fill=text_color, anchor="mt")

    # --- טבלה: נמוכה יותר וצפופה יותר ---
    header_y = 350
    header = fix_text("   עיר        כניסה       יציאה   ")
    draw.text((title_x, header_y), header, font=font_header, fill=gold_color, anchor="mt")
    
    # קו מפריד
    line_y = 380
    draw.line((title_x - 150, line_y, title_x + 150, line_y), fill=text_color, width=2)

    # שורות הטבלה
    rows_y = 410
    row_space = 45 # רווח צפוף יותר
    
    for row in times:
        city = fix_text(row['city'])
        draw.text((title_x + 100, rows_y), city, font=font_text, fill=text_color, anchor="rt")
        draw.text((title_x, rows_y), row['candles'], font=font_text, fill=text_color, anchor="mt")
        draw.text((title_x - 100, rows_y), row['havdalah'], font=font_text, fill=text_color, anchor="lt")
        rows_y += row_space

    img.save("shabbat_final.jpg")
    return "shabbat_final.jpg"

def send_photo(image_path, caption):
    print(f"Sending to {CHANNEL_ID}...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def main():
    print("Starting TEST run...")
    if True: 
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "בדיקת מיקומים סופית - הכל תוקן והונמך")

if __name__ == "__main__":
    main()
