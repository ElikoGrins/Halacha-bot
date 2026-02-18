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
CHANNEL_ID = "269175916"
CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"},
    {"name": "אילת", "geonameid": "295277"}
]

# --- פונקציות עזר לעברית ---
def fix_text(text):
    """מסדר עברית שתהיה קריאה מימין לשמאל בתמונה"""
    if not text: return ""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

# --- פונקציות שבת ---
def get_shabbat_times():
    """מקבל את זמני השבת והפרשה"""
    today = datetime.date.today()
    # מוצא את התאריך של יום שישי הקרוב
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
            rabenu = "" # הכנה לרבנו תם אם תרצה בעתיד
            
            for item in data["items"]:
                if item["category"] == "candles":
                    candles = item["title"].split(": ")[1]
                elif item["category"] == "havdalah":
                    havdalah = item["title"].split(": ")[1]
                elif item["category"] == "parashat":
                    parasha_name = item["hebrew"]
            
            results.append({
                "city": city["name"],
                "candles": candles,
                "havdalah": havdalah
            })
        except Exception as e:
            print(f"Error fetching data for {city['name']}: {e}")
            
    return parasha_name, results

def create_shabbat_image(parasha, times):
    """יוצר את התמונה המעוצבת"""
    try:
        img = Image.open("shabbat_bg.jpg")
    except:
        print("Error: shabbat_bg.jpg not found. Creating white background.")
        img = Image.new('RGB', (1080, 1350), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # טעינת הפונטים (במידה והקובץ קיים)
    try:
        font_title = ImageFont.truetype("Assistant-Bold.ttf", 90)
        font_text = ImageFont.truetype("Assistant-Bold.ttf", 60)
        font_logo = ImageFont.truetype("Assistant-Bold.ttf", 45)
    except:
        font_title = font_text = font_logo = ImageFont.load_default()

    # צבעים
    text_color = (50, 50, 50)  # אפור כהה מאוד
    gold_color = (184, 134, 11) # זהב
    
    # 1. לוגו בצד שמאל למעלה (במקום ערוץ 2000)
    logo_text = "2HalahotBeyom"
    draw.text((30, 30), logo_text, font=font_logo, fill=text_color)

    # 2. כותרת ראשית: שבת פרשת...
    title_text = fix_text(f"שבת פרשת {parasha}")
    # ממקם במרכז (בערך גובה 150-200 מהלמעלה)
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    w_text = bbox[2] - bbox[0]
    draw.text(((W - w_text) / 2, 180), title_text, font=font_title, fill=text_color)

    # 3. כותרות הטבלה
    header = fix_text("   עיר        כניסה       יציאה   ")
    bbox_head = draw.textbbox((0, 0), header, font=font_text)
    w_head = bbox_head[2] - bbox_head[0]
    draw.text(((W - w_head) / 2, 400), header, font=font_text, fill=gold_color)

    # קו מפריד מתחת לכותרת
    draw.line((100, 480, W - 100, 480), fill=text_color, width=3)

    # 4. מילוי הנתונים
    start_y = 530
    row_height = 110 # רווח בין שורות
    
    for row in times:
        city_text = fix_text(row['city'])
        candles_text = row['candles']
        havdalah_text = row['havdalah']

        # עיר (ימין)
        draw.text((W - 200, start_y), city_text, font=font_text, fill=text_color, anchor="rs")
        
        # כניסה (אמצע)
        draw.text((W / 2, start_y), candles_text, font=font_text, fill=text_color, anchor="ms")
        
        # יציאה (שמאל)
        draw.text((200, start_y), havdalah_text, font=font_text, fill=text_color, anchor="ls")

        start_y += row_height

    output_filename = "shabbat_final.jpg"
    img.save(output_filename)
    return output_filename

def send_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as img_file:
        data = {'chat_id': CHANNEL_ID, 'caption': caption}
        files = {'photo': img_file}
        requests.post(url, data=data, files=files)

# --- הלכות רגילות ---
def get_random_halachot():
    with open('halachot.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return random.sample(lines, 2)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHANNEL_ID, 'text': text}
    requests.post(url, json=payload)

# --- MAIN ---
def main():
    # בדיקת יום בשבוע (0=שני, ..., 4=שישי, 5=שבת, 6=ראשון)
    # שים לב: בשרתי גיטהב לפעמים השעון הוא UTC.
    # ליתר ביטחון נוודא שאנחנו לא בשבת
    
    weekday = datetime.datetime.now().weekday()
    
    # יום שבת הוא 5 בפייתון
    if weekday == 5:
        print("Shabbat Shalom! Bot is resting.")
        return # עצירה מוחלטת
    
    # יום שישי הוא 4 בפייתון
    if True: # בדיקה
        print("It's Friday! Generating Shabbat times...")
        parasha, times = get_shabbat_times()
        image_path = create_shabbat_image(parasha, times)
        caption = "שבת שלום ומבורך לכל עם ישראל! 🕯️🍷"
        send_photo(image_path, caption)
        
    else:
        # ימים ראשון (6), שני (0), שלישי (1), רביעי (2), חמישי (3)
        print("Regular day. Sending Halachot...")
        halachot = get_random_halachot()
        message = f"🌟 **הלכה יומית** 🌟\n\n1. {halachot[0]}\n\n2. {halachot[1]}\n\nיום מבורך! ✨"
        send_telegram_message(message)

if __name__ == "__main__":
    main()
