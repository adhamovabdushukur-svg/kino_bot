import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import sqlite3
from flask import Flask
from threading import Thread

# BotFather'dan olingan tokenni shu yerga yozing
TOKEN = os.environ.get('BOT_TOKEN', '8742765068:AAHnaLpcW88HFVo4dkM7iR2-bjPR3xEvzX4')
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'movies.json'
DB_FILE = 'database.db'
REQUIRED_CHANNEL = os.environ.get('CHANNEL_ID', '@abdurahim2011') # Majburiy a'zolik kanali

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            code INTEGER PRIMARY KEY,
            file_id TEXT
        )
    ''')
    
    # Migratsiya: Agar eski movies.json bo'lsa, undan ma'lumotlarni bazaga o'tkazamiz
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            
            if data.get('admin_id') is not None:
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_id', ?)", (str(data['admin_id']),))
            
            for code, file_id in data.get('movies', {}).items():
                cursor.execute("INSERT OR IGNORE INTO movies (code, file_id) VALUES (?, ?)", (int(code), file_id))
            
            conn.commit()
            # Qayta migratsiya bo'lmasligi uchun fayl nomini o'zgartirib qo'yamiz
            os.rename(DATA_FILE, 'movies_backup.json')
            print("Ma'lumotlar JSON dan SQLite ga o'tkazildi.")
        except Exception as e:
            print(f"Migratsiyada xatolik: {e}")

    conn.commit()
    conn.close()

def get_admin_id():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='admin_id'")
    row = cursor.fetchone()
    conn.close()
    return int(row[0]) if row and row[0] != 'None' else None

def set_admin_id(admin_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_id', ?)", (str(admin_id),))
    conn.commit()
    conn.close()

def add_movie(file_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(code) FROM movies")
    row = cursor.fetchone()
    next_code = 100 if row[0] is None else row[0] + 1
    cursor.execute("INSERT INTO movies (code, file_id) VALUES (?, ?)", (next_code, file_id))
    conn.commit()
    conn.close()
    return next_code

def get_movie(code):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM movies WHERE code=?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Bazani ishga tushirish
init_db()

def check_subscription(user_id):
    try:
        # Foydalanuvchining kanaldagi holatini tekshirish
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Obunani tekshirishda xatolik: {e}")
        # Agar bot kanalda admin bo'lmasa, xatolik beradi
        return False

def get_subscription_keyboard():
    markup = InlineKeyboardMarkup()
    # url qismida kanal linki shakllantiriladi
    channel_url = f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"
    markup.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=channel_url))
    markup.add(InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_sub"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    admin_id = get_admin_id()
    if admin_id is None:
        bot.reply_to(message, "Assalomu alaykum! Bot hozircha sozlanmagan.\nAdmin bo'lish uchun /setadmin buyrug'ini yuboring.")
        return

    # Obunani tekshirish (admin uchun majburiy emas, lekin oddiy foydalanuvchilar uchun)
    if message.from_user.id != admin_id and not check_subscription(message.from_user.id):
        bot.reply_to(message, "❌ **Botdan foydalanish uchun homiy kanalimizga obuna bo'lishingiz kerak!**\n\nIltimos, pastdagi tugma orqali kanalga a'zo bo'ling va 'Tasdiqlash' tugmasini bosing.", reply_markup=get_subscription_keyboard(), parse_mode='Markdown')
        return

    bot.reply_to(message, "Assalomu alaykum! 🎬 Kino qidirish botiga xush kelibsiz.\n\nKino kodini yuboring (masalan: 100) va men sizga videoni yuboraman.")

@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    admin_id = get_admin_id()
    if admin_id is None:
        set_admin_id(message.from_user.id)
        bot.reply_to(message, "✅ Tabriklayman! Siz bot admini bo'ldingiz.\n\nEndi menga istalgan videoni yuboring (yoki kanaldan forward qiling) va men unga avtomatik tarzda kino kodini (100 dan boshlab) berib, bazaga saqlayman.")
    elif admin_id == message.from_user.id:
        bot.reply_to(message, "Siz allaqachon adminsiz. Menga kino yuboring va kino bazasini to'ldiring!")
    else:
        bot.reply_to(message, "Kechirasiz, admin allaqachon tayinlangan.")

# Video kelganda ishlashi uchun
@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    admin_id = get_admin_id()
    
    # Agar xabar yuborgan odam admin bo'lsa
    if admin_id == message.from_user.id:
        if message.content_type == 'video':
            file_id = message.video.file_id
        else:
            file_id = message.document.file_id
            
        next_code = add_movie(file_id)
        
        bot.reply_to(message, f"✅ Video bazaga muvaffaqiyatli saqlandi!\n\n🎬 Kino kodi: `{next_code}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Kechirasiz, faqat admin kino qo'sha oladi.")

# Tasdiqlash tugmasi bosilganda
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Obunangiz tasdiqlandi! Rahmat.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Tabriklaymiz! Endi menga kino kodini yuborishingiz mumkin. 🎬")
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def send_movie(message):
    admin_id = get_admin_id()
    
    # Obunani tekshirish
    if not message.text.startswith('/'):
        if admin_id is not None and message.from_user.id != admin_id:
            if not check_subscription(message.from_user.id):
                bot.reply_to(message, "❌ **Kino yuklab olish uchun kanalimizga obuna bo'lishingiz kerak!**\n\nIltimos, pastdagi tugma orqali kanalga a'zo bo'ling va 'Tasdiqlash' tugmasini bosing.", reply_markup=get_subscription_keyboard(), parse_mode='Markdown')
                return

    movie_code = message.text.strip()
    
    if movie_code.isdigit():
        file_id = get_movie(int(movie_code))
        if file_id:
            try:
                bot.send_video(chat_id=message.chat.id, video=file_id, caption=f"🎬 Kino kodi: {movie_code}\n📢 Bizning kanal: {REQUIRED_CHANNEL}")
            except Exception as e:
                try:
                    bot.send_document(chat_id=message.chat.id, document=file_id, caption=f"🎬 Kino kodi: {movie_code}\n📢 Bizning kanal: {REQUIRED_CHANNEL}")
                except:
                    bot.reply_to(message, "❌ Kechirasiz, videoni yuklashda xatolik yuz berdi. Bu fayl video emas bo'lishi mumkin.")
                    print(f"Xatolik: {e}")
        else:
            bot.reply_to(message, "❌ Kechirasiz, bu kod bilan kino topilmadi.\nIltimos, to'g'ri kod yuboring.")
    else:
        if not movie_code.startswith('/'):
            bot.reply_to(message, "❌ Kechirasiz, kino kodi faqat raqamlardan iborat bo'lishi kerak.")

app = Flask(__name__)

@app.route('/')
def home():
    return "Kino Bot ishlayapti!"

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    # Render uchun majburiy veb-serverni orqa fonda ishga tushirish
    server_thread = Thread(target=run_http_server)
    server_thread.start()

    print("Bot ishga tushdi...")
    bot.polling(none_stop=True)
