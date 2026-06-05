# Telegram Kino Bot

Bu bot Telegram kanallari orqali kinolarni avtomatik tarzda raqamlash va qidirish imkonini beradi. Baza sifatida JSON ishlatiladi. Majburiy a'zolik funksiyasiga ega.

## Imkoniyatlari:
- Majburiy obuna (kanalga a'zo bo'lmaguniga qadar bot ishlamaydi)
- Avtomatik kod biriktirish (botga yuborilgan videolarga o'zi kod beradi, masalan 100, 101)
- Bot o'chib yonganda ham ma'lumotlarni saqlab qolish (JSON baza)
- Admin paneli (`/setadmin` orqali)

## Qanday ishga tushiriladi?
1. Kerakli kutubxonalarni o'rnating: `pip install -r requirements.txt`
2. `bot.py` fayli ichidagi `TOKEN` va `REQUIRED_CHANNEL` sozlamalarini o'zingizga moslang.
3. Dasturni ishga tushiring: `python bot.py` (yoki windows uchun `botni_yoqish.bat` orqali).
4. Botga kirib `/setadmin` buyrug'ini yuboring va kino yuklashni boshlang!
