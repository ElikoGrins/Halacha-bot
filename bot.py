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
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text

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
                    # תיקון כפילות: אם כתוב "פרשת נח", נמחק את ה"פרשת" כדי שלא יהיה פעמיים
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
    
    # פונטים מוקטנים משמעותית
    try:
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 30)   # היה 40+
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 45)  # היה 60+
        font_header = ImageFont.truetype("Assistant-Bold.ttf", 30) # כותרת טבלה
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 30)   # תוכן טבלה
    except:
        font_logo = font_title = font_header = font_text = ImageFont.load_default()

    text_color = (40, 40, 40)
    gold_color = (180, 130, 20)

    # --- תיקון 1: לוגו קטן בצד שמאל למעלה ---
    # anchor="lt" אומר Left Top - הפינה השמאלית העליונה של הטקסט
    draw.text((40, 40), "2HalahotBeyom", font=font_logo, fill=text_color, anchor="lt")

    # --- תיקון 2: הטקסט בצד ימין למעלה ---
    # אנחנו מיישרים הכל לפי הקו הימני (W - 50)
    right_margin = W - 50
    current_y = 50

    # כותרת ראשית (פרשת השבוע)
    # שימוש ב-fix_text כדי שהעברית לא תהיה הפוכה
    full_title = fix_text(f"שבת פרשת {parasha}")
    # anchor="rt" אומר Right Top - מיישר את הטקסט לימין
    draw.text((right_margin, current_y), full_title, font=font_title, fill=text_color, anchor="rt")

    # כותרות טבלה
    current_y += 80
    header = fix_text("   עיר        כניסה       יציאה   ")
    draw.text((right_margin, current_y), header, font=font_header, fill=gold_color, anchor="rt")
    
    # קו מפריד קטן
    current_y += 40
    draw.line((right_margin - 350, current_y, right_margin, current_y), fill=text_color, width=2)

    # שורות הטבלה
    current_y += 20
    row_space = 45 
    
    for row in times:
        city = fix_text(row['city'])
        
        # בניית השורה ידנית כדי לשלוט ברווחים
        # עיר - בצד ימין
        draw.text((right_margin, current_y), city, font=font_text, fill=text_color, anchor="rt")
        
        # כניסה - זזה שמאלה (כ-130 פיקסלים מהימין)
        draw.text((right_margin - 160, current_y), row['candles'], font=font_text, fill=text_color, anchor="rt")
        
        # יציאה - עוד שמאלה (כ-280 פיקסלים מהימין)
        draw.text((right_margin - 300, current_y), row['havdalah'], font=font_text, fill=text_color, anchor="rt")
        
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
        send_photo(path, "בדיקת עיצוב - תיקון עברית הפוכה, כפילות וגדלים")

if __name__ == "__main__":
    main()
