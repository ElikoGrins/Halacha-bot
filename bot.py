import os
import requests
import random
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות לבדיקה ---
TOKEN = os.environ.get("BOT_TOKEN")
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
    
    font_shofar = "Shofar-Bold.ttf"
    font_assistant = "Assistant-Bold.ttf"
    
    try:
        font_logo = ImageFont.truetype(font_shofar, 18)
        font_main_title = ImageFont.truetype(font_assistant, 26)
        font_parasha = ImageFont.truetype(font_shofar, 24)
        font_header = ImageFont.truetype(font_shofar, 16) 
        font_text = ImageFont.truetype(font_shofar, 16)   
        font_dedication = ImageFont.truetype(font_shofar, 20)
    except:
        font_logo = font_main_title = font_parasha = font_header = font_text = font_dedication = ImageFont.load_default()

    black_color = (0, 0, 0)
    text_color = (40, 40, 40)
    highlight_color = (20, 50, 100) 
    gold_bright = (255, 215, 0)    

    # 1. לוגו - פינה שמאלית
    draw.text((15, 10), "2HalahotBeyom", font=font_logo, fill=highlight_color, anchor="lt")

    # 2. כותרות - ימין
    right_edge = W - 30 
    top_y = 25
    title_text = "זמני כניסת ויציאת שבת"
    draw.text((right_edge, top_y), title_text, font=font_main_title, fill=black_color, anchor="rt")
    
    title_bbox = draw.textbbox((right_edge, top_y), title_text, font=font_main_title, anchor="rt")
    title_center_x = (title_bbox[0] + title_bbox[2]) / 2
    
    current_y = top_y + 35 # צמצום רווח מתחת לכותרת
    draw.text((title_center_x, current_y), f"פרשת {parasha}", font=font_parasha, fill=gold_bright, anchor="mt")

    # 3. טבלה מהודקת
    x_city = right_edge         
    x_candles = right_edge - 90  
    x_havdalah = right_edge - 170 

    current_y += 45 # צמצום רווח לכותרות הטבלה
    draw.text((x_candles, current_y), "כניסה", font=font_header, fill=highlight_color, anchor="mt")
    draw.text((x_havdalah, current_y), "יציאה", font=font_header, fill=highlight_color, anchor="mt")
    
    current_y += 22 # צמצום רווח לקו המפריד
    draw.line((x_havdalah - 35, current_y, x_city, current_y), fill=text_color, width=2)

    current_y += 10 # צמצום רווח לשורה הראשונה
    for row in times:
        draw.text((x_city, current_y), row['city'], font=font_text, fill=text_color, anchor="rt")
        draw.text((x_candles, current_y), row['candles'], font=font_text, fill=text_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="mt")
        current_y += 26 # צמצום רווח בין שורות (מ-30 ל-26)

    # 4. הקדשה
    current_y += 30 # צמצום רווח להקדשה
    draw.text((right_edge, current_y), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=highlight_color, anchor="rt")

    img.save("shabbat_test.jpg")
    return "shabbat_test.jpg"

def main():
    parasha, times = get_shabbat_times()
    path = create_shabbat_image(parasha, times)
    send_photo(path, "טסט עיצוב: טבלה מהודקת ורווחים מצומצמים")

def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

if __name__ == "__main__":
    main()
