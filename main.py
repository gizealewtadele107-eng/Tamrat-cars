import os
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- Render እንዳይዘጋ የሚያደርግ ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "ቦቱ እየሰራ ነው!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- የቦቱ ቅንብሮች ---
TOKEN = "8466476114:AAEQqcA0r6LcwsBKTZuZxdZRfM2qmFDViSE"
CAR_SELECTION, NAME, PHONE, SCREENSHOT = range(4)

# የመኪና ዋጋ ዝርዝር
PRICES = {"Sino": "2000 ETB", "Isuzu": "1500 ETB", "Toyota": "1000 ETB"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, proof TEXT)''')
    conn.close()

async def start(update, context):
    kb = [["Sino", "Isuzu"], ["Toyota"]]
    await update.message.reply_text(
        "እንኳን ወደ መኪና ዕጣ ቦት መጡ! 🚗\nእባክዎ መሳተፍ የሚፈልጉበትን መኪና ይምረጡ፦",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update, context):
    car = update.message.text
    if car not in PRICES:
        await update.message.reply_text("እባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ።")
        return CAR_SELECTION
    context.user_data['car'] = car
    await update.message.reply_text(f"የመረጡት፦ {car}\nዋጋ፦ {PRICES[car]}\nአሁን ሙሉ ስምዎን ያስገቡ፦")
    return NAME

async def get_name(update, context):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("አሁን ስልክ ቁጥርዎን ያስገቡ፦")
    return PHONE

async def get_phone(update, context):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text(
        f"ለክፍያ ስልክ፦ 0912345678 (Telebirr)\nእባክዎ የከፈሉበትን ስክሪንሾት (Screenshot) እዚህ ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update, context):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        car = context.user_data.get('car')
        name = context.user_data.get('name')
        phone = context.user_data.get('phone')
        
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT INTO users (car, name, phone, proof) VALUES (?, ?, ?, ?)", (car, name, phone, file_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text("✅ እናመሰግናለን! ክፍያዎ ተመዝግቧል። ኦፕሬተሩ ሲያረጋግጥ ይደወልልዎታል።")
        return ConversationHandler.END
    else:
        await update.message.reply_text("እባክዎ የክፍያ ማረጋገጫ ምስል (Screenshot) ይላኩ።")
        return SCREENSHOT

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CAR_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)]
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    application.run_polling()
