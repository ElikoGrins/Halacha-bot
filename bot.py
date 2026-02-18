import os
import requests
import random
import datetime
import json
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "269175916" 

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"}
]

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
                    parasha_name = item["hebrew"].replace("פרשת ", "")
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
    
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 25)
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 25)
        font_header = ImageFont.truetype("Assistant-Bold.ttf", 18)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 18)
    except:
        font_logo = font_title = font_header = font_text = ImageFont.load_default()

    text_color = (40, 40, 40)
    gold_color = (180, 130, 20)

    # --- 1. לוגו: הוזז שמאלה ולמעלה (מעל הלהבה) ---
    # היה ב-60,30. עכשיו ב-30,20.
    draw.text((30, 20), "2HalahotBeyom", font=font_logo, fill=text_color, anchor="lt")

    # --- 2. טבלה וכותרות ---
    # קובעים נקודות עוגן קבועות לכל עמודה כדי שהכל יהיה מיושר פלס
    right_margin = W - 50  # קו ימין של התמונה
    
    # מיקומי ה-X של העמודות:
    x_city = right_margin         # עמודת עיר (מיושרת לימין)
    x_candles = right_margin - 180 # עמודת כניסה (ממורכזת)
    x_havdalah = right_margin - 320 # עמודת יציאה (ממורכזת)

    current_y = 50

    # כותרת: עברית רגילה (בלי היפוך)
    full_title = f"שבת פרשת {parasha}"
    draw.text((x_city, current_y), full_title, font=font_title, fill=text_color, anchor="rt")

    # כותרות טבלה
    current_y += 50
    # עיר - מיושרת לימין
    draw.text((x_city, current_y), "עיר", font=font_header, fill=gold_color, anchor="rt")
    # כניסה - ממורכזת לפי העמודה שלה
    draw.text((x_candles, current_y), "כניסה", font=font_header, fill=gold_color, anchor="mt")
    # יציאה - ממורכזת לפי העמודה שלה
    draw.text((x_havdalah, current_y), "יציאה", font=font_header, fill=gold_color, anchor="mt")
    
    # קו מפריד
    current_y += 30
    draw.line((x_havdalah - 40, current_y, x_city, current_y), fill=text_color, width=2)

    # שורות הטבלה
    current_y += 20
    row_space = 30 
    
    for row in times:
        # עיר (ימין)
        draw.text((x_city, current_y), row['city'], font=font_text, fill=text_color, anchor="rt")
        
        # כניסה (אמצע - ממורכז) - המספרים יושבים בול מתחת לכותרת
        draw.text((x_candles, current_y), row['candles'], font=font_text, fill=text_color, anchor="mt")
        
        # יציאה (שמאל - ממורכז)
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="mt")
        
        current_y += row_space

    img.save("shabbat_final.jpg")
    return "shabbat_final.jpg"

def send_photo(image_path, caption):
    print(f"Sending to {CHANNEL_ID}...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def main():
    print("Starting TEST run - No Reversal + Alignment Fix")
    if True: 
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "בדיקת עיצוב סופית - הכל ישר ומיושר")

if __name__ == "__main__":
    main()
