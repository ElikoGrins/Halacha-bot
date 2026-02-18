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

# --- מצב בדיקה: שולח ל-ID שלך ---
CHANNEL_ID = "269175916" 
# כשתסיים לבדוק, תחזיר את השורה למטה ותמחק את השורה למעלה:
# CHANNEL_ID = os.environ.get("CHANNEL_ID")

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"}
    # אילת הוסרה לבקשתך
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
    print("Creating image layout...")
    # שימוש בתמונה המקורית (לרוחב) כרקע
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        img = Image.open("image.png")
    else:
        # גיבוי למקרה שהתמונה לא נמצאת
        img = Image.new('RGB', (1200, 800), color=(240, 240, 235))

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # פונטים (הקטנתי מעט שיתאים לאזור החדש)
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 50)
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 65)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 45)
    except:
        font_logo = font_title = font_text = ImageFont.load_default()

    text_color = (40, 40, 40)
    gold_color = (180, 130, 20)

    # --- מיקום 1: לוגו בצד שמאל למעלה (ריבוע כחול) ---
    draw.text((50, 50), "2HalahotBeyom", font=font_logo, fill=text_color)

    # --- מיקום 2: טבלה בצד ימין (ריבוע אדום) ---
    # מגדירים את מרכז האזור הימני
    right_area_center_x = W * 0.75 
    start_y = H * 0.25 # התחלה בערך ברבע הגובה

    # כותרת ראשית
    title = fix_text(f"שבת פרשת {parasha}")
    draw.text((right_area_center_x, start_y), title, font=font_title, fill=text_color, anchor="ms")

    # כותרות טבלה
    header_y = start_y + 100
    header = fix_text("   עיר        כניסה       יציאה   ")
    draw.text((right_area_center_x, header_y), header, font=font_text, fill=gold_color, anchor="ms")
    
    # קו מפריד (קצר יותר, מותאם לאזור)
    line_y = header_y + 60
    draw.line((right_area_center_x - 200, line_y, right_area_center_x + 200, line_y), fill=text_color, width=2)

    # שורות הטבלה
    rows_y = line_y + 50
    row_space = 70
    for row in times:
        city = fix_text(row['city'])
        # מיקומים יחסיים למרכז האזור הימני
        draw.text((right_area_center_x + 150, rows_y), city, font=font_text, fill=text_color, anchor="rs")
        draw.text((right_area_center_x, rows_y), row['candles'], font=font_text, fill=text_color, anchor="ms")
        draw.text((right_area_center_x - 150, rows_y), row['havdalah'], font=font_text, fill=text_color, anchor="ls")
        rows_y += row_space

    img.save("shabbat_final.jpg")
    return "shabbat_final.jpg"

def send_photo(image_path, caption):
    print(f"Sending to {CHANNEL_ID}...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

# --- פונקציה ראשית לבדיקה ---
def main():
    print("Starting TEST run...")
    # מכריחים ריצה לבדיקה
    if True: 
        parasha, times = get_shabbat_times()
        image_path = create_shabbat_image(parasha, times)
        send_photo(image_path, "בדיקת מיקומים סופית (בלי אילת)")

if __name__ == "__main__":
    main()
