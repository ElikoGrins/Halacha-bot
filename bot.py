import os
import requests
import random
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות לבדיקה ---
TOKEN = os.environ.get("BOT_TOKEN")
# שולח אליך לפרטי לצורך הטסט
CHANNEL_ID = "269175916" 

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
    parasha_name = ""
    
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
                elif item["category"] == "parashat":
                    parasha_name = item["hebrew"].replace("פרשת ", "")
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except Exception as e:
            print(f"Error: {e}")
    return parasha_name, results

def create_shabbat_image(parasha, times):
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        img = Image.open("image.png")
    else:
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # טעינת פונט שופר (וודא שהעלית קובץ בשם זה!)
    font_path = "Shofar-Bold.ttf"
    try:
        font_main_title = ImageFont.truetype(font_path, 32)
        font_parasha = ImageFont.truetype(font_path, 28)
        font_logo = ImageFont.truetype(font_path, 26)
        font_header = ImageFont.truetype(font_path, 22)
        font_text = ImageFont.truetype(font_path, 22)
        font_dedication = ImageFont.truetype(font_path, 22)
    except:
        font_main_title = font_parasha = font_logo = font_header = font_text = font_dedication = ImageFont.load_default()

    black_color = (0, 0, 0)
    text_color = (40, 40, 40)
    highlight_color = (20, 50, 100) # כחול מלכותי (לכותרות כניסה/יציאה וללוגו)
    gold_bright = (255, 215, 0)    # זהב בוהק
    bronze_color = (160, 110, 40)  # זהב-חום (להקדשה)

    # 1. לוגו כחול - למעלה משמאל
    draw.text((20, 15), "2HalahotBeyom", font=font_logo, fill=highlight_color, anchor="lt")

    # 2. כותרות וטבלה - ימין
    right_edge = W - 20 
    x_city = right_edge         
    x_candles = right_edge - 110  
    x_havdalah = right_edge - 200 

    current_y = 40
    
    # כותרת ראשית שחורה מודגשת
    draw.text((x_city, current_y), "זמני כניסת ויציאת שבת", font=font_main_title, fill=black_color, anchor="rt")
    
    # פרשת השבוע בזהב בוהק
    current_y += 45
    draw.text((x_city, current_y), f"פרשת {parasha}", font=font_parasha, fill=gold_bright, anchor="rt")

    # כותרות טבלה (ללא "עיר")
    current_y += 55
    draw.text((x_candles, current_y), "כניסה", font=font_header, fill=highlight_color, anchor="mt")
    draw.text((x_havdalah, current_y), "יציאה", font=font_header, fill=highlight_color, anchor="mt")
    
    # קו מפריד
    current_y += 35
    draw.line((x_havdalah - 40, current_y, x_city, current_y), fill=text_color, width=3)

    # שורות הטבלה (שמות ערים וזמנים)
    current_y += 20
    for row in times:
        draw.text((x_city, current_y), row['city'], font=font_text, fill=text_color, anchor="rt")
        draw.text((x_candles, current_y), row['candles'], font=font_text, fill=text_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="mt")
        current_y += 35

    # 3. הקדשה
    current_y += 45
    draw.text((x_city, current_y), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=bronze_color, anchor="rt")

    img.save("shabbat_test.jpg")
    return "shabbat_test.jpg"

def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def main():
    parasha, times = get_shabbat_times()
    path = create_shabbat_image(parasha, times)
    send_photo(path, "בדיקת עיצוב: כותרת שחורה, פרשה בזהב, ללא 'עיר'")

if __name__ == "__main__":
    main()
