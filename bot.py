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
    print("Fetching times for test...")
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
    print("Creating image with Keter font...")
    # טעינת רקע
    if os.path.exists("Shabbat_bg.jpg.JPG"):
        img = Image.open("Shabbat_bg.jpg.JPG")
    elif os.path.exists("image.png"):
        img = Image.open("image.png")
    else:
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # פונט כתר - וודא שהשם תואם למה שהעלית!
    font_path = "KeterYG-Bold.ttf"
    try:
        font_logo = ImageFont.truetype(font_path, 26)
        font_title = ImageFont.truetype(font_path, 28)
        font_header = ImageFont.truetype(font_path, 20)
        font_text = ImageFont.truetype(font_path, 20)
        font_dedication = ImageFont.truetype(font_path, 22)
        print("Success: Keter font loaded.")
    except:
        print("Warning: Keter font not found, using default.")
        font_logo = font_title = font_header = font_text = font_dedication = ImageFont.load_default()

    text_color = (40, 40, 40)
    highlight_color = (20, 50, 100) # כחול מלכותי
    bronze_color = (160, 110, 40)  # זהב-חום

    # 1. לוגו כחול - למעלה משמאל
    draw.text((20, 15), "2HalahotBeyom", font=font_logo, fill=highlight_color, anchor="lt")

    # 2. טבלה - ימין
    right_edge = W - 20 
    x_city, x_candles, x_havdalah = right_edge, right_edge - 110, right_edge - 200 

    current_y = 50
    draw.text((x_city, current_y), f"שבת פרשת {parasha}", font=font_title, fill=text_color, anchor="rt")

    current_y += 55
    draw.text((x_city, current_y), "עיר", font=font_header, fill=highlight_color, anchor="rt")
    draw.text((x_candles, current_y), "כניסה", font=font_header, fill=highlight_color, anchor="mt")
    draw.text((x_havdalah, current_y), "יציאה", font=font_header, fill=highlight_color, anchor="mt")
    
    current_y += 35
    draw.line((x_havdalah - 40, current_y, x_city, current_y), fill=text_color, width=3)

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
    # בבדיקה אנחנו מריצים הכל בלי לבדוק יום ושעה
    parasha, times = get_shabbat_times()
    path = create_shabbat_image(parasha, times)
    send_photo(path, "טסט לעיצוב שבת עם פונט כתר - בדיקת מיקומים וצבעים")
    print("Test image sent to your private chat!")

if __name__ == "__main__":
    main()
