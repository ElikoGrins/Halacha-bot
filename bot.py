import os
import requests
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- הגדרות טלגרם ---
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# --- הגדרות WhatsApp (Green API) ---
GREEN_API_HOST = "https://7103.api.greenapi.com" 
GREEN_API_ID = os.environ.get("GREEN_API_ID")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")
WA_GROUP_ID = os.environ.get("WA_GROUP_ID")

CITIES = [
    {"name": "ירושלים", "geonameid": "281184"},
    {"name": "תל אביב", "geonameid": "293397"},
    {"name": "חיפה", "geonameid": "294801"},
    {"name": "באר שבע", "geonameid": "295530"}
]

def draw_telegram_icon(draw, x, y, size):
    bg_color = (36, 161, 222)
    draw.ellipse([x, y, x + size, y + size], fill=bg_color)
    p = [(x+size*0.25, y+size*0.5), (x+size*0.75, y+size*0.3), (x+size*0.6, y+size*0.7), (x+size*0.5, y+size*0.55)]
    draw.polygon(p, fill="white")

def get_shabbat_times():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    date_str = friday.strftime("%Y-%m-%d")
    results = []
    parashah_name = ""
    
    for city in CITIES:
        url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city['geonameid']}&date={date_str}&M=on"
        try:
            response = requests.get(url)
            data = response.json()
            candles, havdalah = "", ""
            for item in data["items"]:
                if item["category"] == "parashat" and not parashah_name:
                    parashah_name = item.get("hebrew", item.get("title"))
                elif item["category"] == "candles":
                    candles = item["title"].split(": ")[1]
                elif item["category"] == "havdalah":
                    havdalah = item["title"].split(": ")[1]
            results.append({"city": city["name"], "candles": candles, "havdalah": havdalah})
        except Exception as e:
            print(f"Error fetching times for {city['name']}: {e}")
            
    if not parashah_name:
        parashah_name = "שבת שלום ומבורך"
        
    return results, parashah_name

def create_shabbat_image(times, parashah_name):
    try:
        img = Image.open("shabbat_template.JPG")
    except Exception as e:
        print(f"שגיאה בטעינת התמונה: {e}")
        img = Image.new('RGB', (1200, 800), color='white')

    draw = ImageDraw.Draw(img)
    W, H = img.size

    black_color = (0, 0, 0)
    gold_color = (155, 95, 25) 
    gold_outline = (90, 50, 10)

    try:
        font_times = ImageFont.truetype("Assistant-Bold.ttf", 58) 
        font_dedication = ImageFont.truetype("Shofar-Bold.ttf", 37) 
        font_parashah = ImageFont.truetype("stam.ttf", 115) 
    except:
        font_times = font_dedication = font_parashah = ImageFont.load_default()
    
    logo_x, logo_y = 30, 30
    icon_size = 37 
    draw_telegram_icon(draw, logo_x, logo_y, icon_size)
    draw.text((logo_x + icon_size + 10, logo_y - 4), "2HalahotBeyom", font=font_dedication, fill=black_color, anchor="lt")

    # הדפסת שם הפרשה
    draw.text((W * 0.69, H * 0.195), parashah_name, font=font_parashah, fill=gold_color, anchor="mm", stroke_width=4, stroke_fill=gold_outline)

    x_candles = W * 0.68  
    x_havdalah = W * 0.53 
    start_y = H * 0.33    
    y_spacing = H * 0.075  

    current_y = start_y
    for row in times:
        draw.text((x_candles, current_y), row['candles'], font=font_times, fill=black_color, anchor="mt")
        draw.text((x_havdalah, current_y), row['havdalah'], font=font_times, fill=black_color, anchor="mt")
        current_y += y_spacing

    draw.text((W - 40, H - 40), "לעילוי נשמת אליהו בן ישועה", font=font_dedication, fill=black_color, anchor="rd")

    final_path = "shabbat_final.jpg"
    img.save(final_path)
    return final_path

def get_sequential_halachot():
    with open('halachot.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        
    if len(lines) < 2:
        return ["אין מספיק הלכות בקובץ", ""]

    start_date = datetime.date(2026, 3, 6) 
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).date()
    
    days_passed = 0
    current_date = start_date
    while current_date < today:
        if current_date.weekday() != 5: 
            days_passed += 1
        current_date += datetime.timedelta(days=1)
        
    index = (days_passed * 2) % len(lines)
    
    h1 = lines[index]
    h2 = lines[(index + 1) % len(lines)] 
    
    return [h1, h2]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text})

def send_telegram_photo(image_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHANNEL_ID, 'caption': caption}, files={'photo': f})

def send_whatsapp_message(text):
    if not all([GREEN_API_ID, GREEN_API_TOKEN, WA_GROUP_ID]):
        return
    url = f"{GREEN_API_HOST}/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {"chatId": WA_GROUP_ID, "message": text}
    requests.post(url, json=payload)

def send_whatsapp_photo(image_path, caption):
    if not all([GREEN_API_ID, GREEN_API_TOKEN, WA_GROUP_ID]):
        return
    url = f"{GREEN_API_HOST}/waInstance{GREEN_API_ID}/sendFileByUpload/{GREEN_API_TOKEN}"
    payload = {"chatId": WA_GROUP_ID, "caption": caption}
    with open(image_path, 'rb') as f:
        files = {'file': (image_path, f, 'image/jpeg')}
        requests.post(url, data=payload, files=files)

# --- פונקציית ספירת העומר (מעודכנת לערב) ---
def get_omer_reminder():
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).date()
    omer_first_night = datetime.date(2026, 4, 2) 
    
    if today == datetime.date(2026, 4, 1):
        return "🌾 תזכורת: מחר בערב מתחילים את ספירת העומר!"
        
    days_to_count = (today - omer_first_night).days + 1
    
    if 1 <= days_to_count <= 49:
        weeks = days_to_count // 7
        days = days_to_count % 7
        
        day_str = "יום אחד" if days_to_count == 1 else "שני ימים" if days_to_count == 2 else f"{days_to_count} ימים"
        
        text = f"🌾 ספירת העומר: הערב סופרים {day_str}"
        
        if weeks > 0:
            week_str = "שבוע אחד" if weeks == 1 else f"{weeks} שבועות"
            text += f", שהם {week_str}"
            
            if days > 0:
                rem_day_str = "ויום אחד" if days == 1 else "ושני ימים" if days == 2 else f"ו-{days} ימים"
                text += f" {rem_day_str}"
                
        text += " לעומר."
        return text
        
    return ""

def main():
    # קביעת השעה לפי שעון ישראל (UTC+3)
    israel_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    current_hour = israel_time.hour
    today = israel_time.date()
    weekday = today.weekday() # 0=שני, ..., 4=שישי, 5=שבת, 6=ראשון

    holidays_2026 = [
        datetime.date(2026, 4, 2),   # פסח - חג ראשון
        datetime.date(2026, 4, 8),   # פסח - שביעי של פסח
        datetime.date(2026, 5, 22),  # חג שבועות
        datetime.date(2026, 9, 12),  # ראש השנה א'
        datetime.date(2026, 9, 13),  # ראש השנה ב'
        datetime.date(2026, 9, 21),  # יום הכיפורים
        datetime.date(2026, 9, 26),  # סוכות - חג ראשון
        datetime.date(2026, 10, 3)   # שמיני עצרת / שמחת תורה
    ]
    is_yom_tov = today in holidays_2026

    # ערבי חגים (למנוע שליחת עומר כשנכנס החג)
    erev_holidays_2026 = [
        datetime.date(2026, 4, 1),   # ערב פסח
        datetime.date(2026, 4, 7),   # ערב שביעי של פסח
        datetime.date(2026, 5, 21),  # ערב שבועות
        datetime.date(2026, 9, 11),  # ערב ראש השנה
        datetime.date(2026, 9, 20),  # ערב כיפור
        datetime.date(2026, 9, 25),  # ערב סוכות
        datetime.date(2026, 10, 2)   # ערב הושענא רבה (שמיני עצרת)
    ]
    is_erev_yom_tov = today in erev_holidays_2026

    # ------------------ ריצת בוקר/צהריים (הלכות) ------------------
    if current_hour < 16:
        if weekday != 5 and not is_yom_tov:
            print("Sending daily halachot...")
            h = get_sequential_halachot() 
            msg = f"2 הלכות יומיות: 📜\n\n1️⃣ {h[0]}\n\n2️⃣ {h[1]}"
            send_telegram_message(msg)
            send_whatsapp_message(msg) 
            print("Halachot sent successfully.")
        
        if weekday == 4 and not is_yom_tov:
            print("Today is Friday. Generating and sending Shabbat image...")
            times, parashah_name = get_shabbat_times()
            path = create_shabbat_image(times, parashah_name)
            caption = "שבת שלום ומבורך! 🕯️🍷"
            send_telegram_photo(path, caption)
            send_whatsapp_photo(path, caption) 
            print("Shabbat image sent successfully.")

    # ------------------ ריצת ערב (ספירת העומר) ------------------
    else:
        # לא שולחים בשישי בערב (ערב שבת) ולא בערב חג
        if weekday != 4 and not is_erev_yom_tov:
            print("Sending Omer reminder...")
            omer_text = get_omer_reminder()
            if omer_text:
                send_telegram_message(omer_text)
                send_whatsapp_message(omer_text)
                print("Omer reminder sent successfully.")

if __name__ == "__main__":
    main()
