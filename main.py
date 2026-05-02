import os
import sqlite3
from flask import Flask
from threading import Thread
from PIL import Image, ImageDraw, ImageFont
import io
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- Render ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "ቦቱ እየሰራ ነው!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- የቦቱ ቅንብሮች ---
TOKEN = "8466476114:AAEQqcA0r6LcwsBKTZuZxdZRfM2qmFDViSE"
OWNER_ID = 7705713321
CAR_SELECTION, NAME, PHONE, PAYMENT_METHOD, SCREENSHOT, QUESTION, BROADCAST = range(7)

PRICES = {"Sino": "2000 ETB", "Isuzu": "1500 ETB", "Toyota": "1000 ETB"}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT)''')
    conn.execute('CREATE TABLE IF NOT EXISTS tickets (number TEXT UNIQUE)')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets")
    if cursor.fetchone()[0] == 0:
        nums = [(str(i),) for i in range(1, 1001)]
        cursor.executemany("INSERT INTO tickets VALUES (?)", nums)
    conn.commit()
    conn.close()

def get_available_ticket():
    conn = sqlite3.connect('lottery.db')
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM tickets WHERE number NOT IN (SELECT ticket FROM users WHERE ticket IS NOT NULL) ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- የቲኬት ፎቶ የመፍጠር ተግባር ---
def create_ticket_image(name, ticket, car):
    # ሰማያዊ ዳራ ያለው ምስል መፍጠር
    img = Image.new('RGB', (600, 400), color=(25, 42, 86))
    d = ImageDraw.Draw(img)
    
    # ጽሁፎችን መጻፍ
    d.text((200, 50), "TAMRAT LOTTERY", fill=(255, 215, 0))
    d.text((50, 150), f"Name: {name}", fill=(255, 255, 255))
    d.text((50, 200), f"Car Type: {car}", fill=(255, 255, 255))
    d.text((50, 250), f"Ticket No: {ticket}", fill=(255, 215, 0))
    d.text((200, 350), "GOOD LUCK!", fill=(0, 255, 0))
    
    # ምስሉን ወደ ባይት መቀየር
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- ባለቤት ማረጋገጫ ---
async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "verify":
        ticket = get_available_ticket()
        if ticket:
            conn = sqlite3.connect('lottery.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, car FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            conn.execute("UPDATE users SET ticket = ?, status = 'Verified' WHERE id = ?", (ticket, user_id))
            conn.commit()
            conn.close()

            # የፎቶ ደረሰኝ መፍጠር
            ticket_img = create_ticket_image(user_data[0], ticket, user_data[1])
            
            await context.bot.send_photo(
                chat_id=user_id, 
                photo=ticket_img, 
                caption=f"✅ ክፍያዎ ተረጋግጧል!\n\nየእርስዎ ቲኬት ቁጥር: {ticket}\nመልካም እድል ይሁንሎ!"
            )
            await query.edit_message_caption(caption=query.message.caption + f"\n\n✅ ጸድቋል! (ቲኬት: {ticket})")
    else:
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ ተሰርዟል!")

# --- (ሌሎቹ የ start, car_chosen, get_name ወዘተ ተግባራት ይቀጥላሉ...)
# --- [ማሳሰቢያ: የቆየውን ኮድ የተቀሩትን ክፍሎች እዚህ ጋር እንዳሉ ይጠቀሙ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("እንኳን ደህና መጡ እጣ ለመቁረጥ ከታች ያለውን ቁልፍ ይጫኑ")
    kb = [["Sino", "Isuzu"], ["Toyota"]]
    await update.message.reply_text("እባክዎ መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text not in PRICES: return CAR_SELECTION
    context.user_data['car'] = update.message.text
    await update.message.reply_text("አሁን ሙሉ ስምዎን (ባለ 3 ቃል) ያስገቡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text.split()) < 3:
        await update.message.reply_text("እባክዎ ስምዎን በትክክል ባለ 3 ቃል ያስገቡ፦")
        return NAME
    context.user_data['name'] = update.message.text
    await update.message.reply_text("አሁን ስልክ ቁጥርዎን ያስገቡ (10 አሃዝ)፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not (text.startswith('0') and len(text) == 10 and text.isdigit()):
        await update.message.reply_text("እባክዎ በትክክል 10 አሃዝ ስልክ ያስገቡ፦")
        return PHONE
    context.user_data['phone'] = text
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["Telebirr", "CBE"]], resize_keyboard=True))
    return PAYMENT_METHOD

async def payment_method_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['payment'] = update.message.text
    await update.message.reply_text(f"{PAYMENT_INFO.get(update.message.text, '')}\n\nክፍያውን ፈጽመው ስክሪንሾት እዚህ ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        d, uid = context.user_data, update.effective_user.id
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT OR REPLACE INTO users (id, car, name, phone, payment, proof, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (uid, d['car'], d['name'], d['phone'], d['payment'], file_id, 'Pending'))
        conn.commit()
        conn.close()
        
        # ለአስተዳዳሪ መላክ
        text = f"🔔 አዲስ ጥያቄ!\n👤 ስም: {d['name']}\n📞 ስልክ: {d['phone']}\n🚗 መኪና: {d['car']}"
        kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"verify_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]]
        await context.bot.send_photo(chat_id=OWNER_ID, photo=file_id, caption=text, reply_markup=InlineKeyboardMarkup(kb))
        
        await update.message.reply_text("✅ መረጃዎ ደርሶናል። ክፍያዎ እንደተረጋገጠ የቲኬት ፎቶ ይደርስዎታል!")
        return ConversationHandler.END
    return SCREENSHOT

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_verification))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CAR_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_method_chosen)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
