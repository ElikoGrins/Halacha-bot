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

# --- מצב בדיקה מופעל (שולח אליך) ---
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
    
    # טעינת התמונה שלך
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        img = Image.open("image.png")
    else:
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # פונטים מותאמים לגודל (קטנים יותר כדי להיכנס בצד)
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 40)  # לוגו קטן
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 55) # כותרת בינונית
        font_header = ImageFont.truetype("Assistant-Bold.ttf", 40) # כותרת טבלה
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 35)   # טקסט טבלה
    except:
        font_logo = font_title = font_header = font_text = ImageFont.load_default()

    text_color = (40, 40, 40)
    gold_color = (180, 130, 20)

    # --- 1. לוגו: פינה שמאלית עליונה (הריבוע הכחול) ---
    draw.text((50, 50), "2HalahotBeyom", font=font_logo, fill=text_color)

    # --- 2. אזור הטקסט: צד ימין (הריבוע האדום) ---
    # אנחנו מגדירים את "מרכז" הטקסט בנקודה שהיא 75% מרוחב התמונה
    # זה דוחף את הכל ימינה לקיר הריק
    center_x = W * 0.78  
    
    # גובה התחלתי
    current_y = H * 0.20 # מתחילים ב-20% מגובה התמונה

    # כותרת ראשית
    title = fix_text(f"שבת פרשת {parasha}")
    draw.text((center_x, current_y), title, font=font_title, fill=text_color, anchor="ms") # ms = Middle (horiz) Top (vert)

    # כותרות טבלה
    current_y += 100
    header = fix_text("   עיר        כניסה       יציאה   ")
    draw.text((center_x, current_y), header, font=font_header, fill=gold_color, anchor="ms")
    
    # קו מפריד
    current_y += 40
    draw.line((center_x - 180, current_y, center_x + 180, current_y), fill=text_color, width=2)

    # שורות הטבלה
    current_y += 40
    row_space = 55 # רווח צפוף יותר בין השורות
    
    for row in times:
        city = fix_text(row['city'])
        
        # חישוב מיקומים יחסיים למרכז הטור הימני
        # עיר בימין
        draw.text((center_x + 130, current_y), city, font=font_text, fill=text_color, anchor="rs") # rs = Right Side anchor
        
        # כניסה באמצע
        draw.text((center_x, current_y), row['candles'], font=font_text, fill=text_color, anchor="ms")
        
        # יציאה בשמאל
        draw.text((center_x - 130, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="ls") # ls = Left Side anchor
        
        current_y += row_space

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
        send_photo(path, "בדיקת מיקומים סופית - הכל בימין")

if __name__ == "__main__":
    main()
