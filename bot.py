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

# פונקציה פשוטה להיפוך עברית (בלי ספריות חיצוניות)
def reverse_hebrew(text):
    if not text: return ""
    return text[::-1]

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
    
    # --- פונטים מוקטנים משמעותית (50% בטבלה, 20% בלוגו) ---
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 25)   # הוקטן מ-30 ל-25
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 25)  # הוקטן מ-35 ל-25
        font_header = ImageFont.truetype("Assistant-Bold.ttf", 18) # הוקטן מ-25 ל-18
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 18)   # הוקטן מ-25 ל-18
    except:
        font_logo = font_title = font_header = font_text = ImageFont.load_default()

    text_color = (40, 40, 40)
    gold_color = (180, 130, 20)

    # --- 1. לוגו: הוקטן, הוזז למעלה וימינה ---
    # היה ב-40,40. הזזתי ל-60,30 (יותר ימינה ולמעלה)
    draw.text((60, 30), "2HalahotBeyom", font=font_logo, fill=text_color, anchor="lt")

    # --- 2. טבלה: הוקטנה ב-50% והוצמדה לימין ---
    right_margin = W - 50
    current_y = 50

    # כותרת: הופכים אותה ידנית כדי שתופיע ישר
    # למשל: "שבת פרשת נח" -> "חנ תשרפ תבש"
    full_title = f"שבת פרשת {parasha}"
    title_reversed = reverse_hebrew(full_title)
    draw.text((right_margin, current_y), title_reversed, font=font_title, fill=text_color, anchor="rt")

    # כותרות טבלה: הופכים רק את המילים בעברית
    current_y += 50
    # "יציאה       כניסה       עיר" (בסדר הפוך כדי שיוצג נכון)
    header_str = "   האיצי        הסינכ       ריע   " 
    draw.text((right_margin, current_y), header_str, font=font_header, fill=gold_color, anchor="rt")
    
    # קו מפריד (קצר יותר כי הפונט קטן)
    current_y += 30
    draw.line((right_margin - 200, current_y, right_margin, current_y), fill=text_color, width=2)

    # שורות הטבלה
    current_y += 20
    row_space = 30 # רווח צפוף יותר
    
    for row in times:
        city_reversed = reverse_hebrew(row['city'])
        
        # בניית השורה: שעה | שעה | עיר
        # בגלל שאנחנו מיישרים לימין (anchor="rt"), אנחנו כותבים:
        # עיר (הכי ימין) -> כניסה -> יציאה
        # אבל בגלל שהטקסט בעיר הפוך, זה ייראה: "םילשורי"
        
        # מיקום העיר (ימין)
        draw.text((right_margin, current_y), city_reversed, font=font_text, fill=text_color, anchor="rt")
        
        # מיקום כניסה (קצת שמאלה)
        draw.text((right_margin - 100, current_y), row['candles'], font=font_text, fill=text_color, anchor="rt")
        
        # מיקום יציאה (עוד שמאלה)
        draw.text((right_margin - 200, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="rt")
        
        current_y += row_space

    img.save("shabbat_final.jpg")
    return "shabbat_final.jpg"

def send_photo(image_path, caption):
    print(f"Sending to {CHANNEL_ID}...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def main():
    print("Starting TEST run - Manual Hebrew Fix")
    if True: 
        parasha, times = get_shabbat_times()
        path = create_shabbat_image(parasha, times)
        send_photo(path, "בדיקת עיצוב - עברית הפוכה ידנית והקטנה מסיבית")

if __name__ == "__main__":
    main()
