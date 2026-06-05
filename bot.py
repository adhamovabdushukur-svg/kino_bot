import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from flask import Flask
from threading import Thread

# BotFather'dan olingan tokenni shu yerga yozing
TOKEN = '8742765068:AAHnaLpcW88HFVo4dkM7iR2-bjPR3xEvzX4'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'movies.json'
REQUIRED_CHANNEL = '@abdurahim2011' # Majburiy a'zolik kanali

# Baza yo'q bo'lsa, yaratamiz
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({"admin_id": None, "movies": {}}, f)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

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
    data = load_data()
    if data['admin_id'] is None:
        bot.reply_to(message, "Assalomu alaykum! Bot hozircha sozlanmagan.\nAdmin bo'lish uchun /setadmin buyrug'ini yuboring.")
        return

    # Obunani tekshirish (admin uchun majburiy emas, lekin oddiy foydalanuvchilar uchun)
    if message.from_user.id != data['admin_id'] and not check_subscription(message.from_user.id):
        bot.reply_to(message, "❌ **Botdan foydalanish uchun homiy kanalimizga obuna bo'lishingiz kerak!**\n\nIltimos, pastdagi tugma orqali kanalga a'zo bo'ling va 'Tasdiqlash' tugmasini bosing.", reply_markup=get_subscription_keyboard(), parse_mode='Markdown')
        return

    bot.reply_to(message, "Assalomu alaykum! 🎬 Kino qidirish botiga xush kelibsiz.\n\nKino kodini yuboring (masalan: 100) va men sizga videoni yuboraman.")

@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    data = load_data()
    if data['admin_id'] is None:
        data['admin_id'] = message.from_user.id
        save_data(data)
        bot.reply_to(message, "✅ Tabriklayman! Siz bot admini bo'ldingiz.\n\nEndi menga istalgan videoni yuboring (yoki kanaldan forward qiling) va men unga avtomatik tarzda kino kodini (100 dan boshlab) berib, bazaga saqlayman.")
    elif data['admin_id'] == message.from_user.id:
        bot.reply_to(message, "Siz allaqachon adminsiz. Menga kino yuboring va kino bazasini to'ldiring!")
    else:
        bot.reply_to(message, "Kechirasiz, admin allaqachon tayinlangan.")

# Video kelganda ishlashi uchun
@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    data = load_data()
    
    # Agar xabar yuborgan odam admin bo'lsa
    if data['admin_id'] == message.from_user.id:
        movies = data['movies']
        
        # Eng katta kodni topamiz, agar bo'sh bo'lsa 100 dan boshlaymiz
        if len(movies) == 0:
            next_code = 100
        else:
            # Mavjud kodlarning eng kattasiga 1 qo'shamiz
            max_code = max([int(k) for k in movies.keys()])
            next_code = max_code + 1
            
        if message.content_type == 'video':
            file_id = message.video.file_id
        else:
            file_id = message.document.file_id
            
        data['movies'][str(next_code)] = file_id
        save_data(data)
        
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
    data = load_data()
    
    # Obunani tekshirish
    if not message.text.startswith('/'):
        if data['admin_id'] is not None and message.from_user.id != data['admin_id']:
            if not check_subscription(message.from_user.id):
                bot.reply_to(message, "❌ **Kino yuklab olish uchun kanalimizga obuna bo'lishingiz kerak!**\n\nIltimos, pastdagi tugma orqali kanalga a'zo bo'ling va 'Tasdiqlash' tugmasini bosing.", reply_markup=get_subscription_keyboard(), parse_mode='Markdown')
                return

    movies = data['movies']
    movie_code = message.text.strip()
    
    if movie_code in movies:
        file_id = movies[movie_code]
        try:
            bot.send_video(chat_id=message.chat.id, video=file_id, caption=f"🎬 Kino kodi: {movie_code}\n📢 Bizning kanal: {REQUIRED_CHANNEL}")
        except Exception as e:
            try:
                bot.send_document(chat_id=message.chat.id, document=file_id, caption=f"🎬 Kino kodi: {movie_code}\n📢 Bizning kanal: {REQUIRED_CHANNEL}")
            except:
                bot.reply_to(message, "❌ Kechirasiz, videoni yuklashda xatolik yuz berdi. Bu fayl video emas bo'lishi mumkin.")
                print(f"Xatolik: {e}")
    else:
        if not movie_code.startswith('/'):
            bot.reply_to(message, "❌ Kechirasiz, bu kod bilan kino topilmadi.\nIltimos, to'g'ri kod yuboring.")

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
