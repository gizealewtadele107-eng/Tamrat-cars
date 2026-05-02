import os
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- Render ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "ቦቱ እየሰራ ነው!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- የቦቱ ቅንብሮች ---
TOKEN = "8466476114:AAEQqcA0r6LcwsBKTZuZxdZRfM2qmFDViSE"
OWNER_ID = 7705713321
CAR_SELECTION, NAME, PHONE, PAYMENT_METHOD, SCREENSHOT, QUESTION = range(6)

PRICES = {"Sino": "2000 ETB", "Isuzu": "1500 ETB", "Toyota": "1000 ETB"}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT)''')
    conn.execute('CREATE TABLE IF NOT EXISTS tickets (number TEXT UNIQUE)')
    conn.execute('CREATE TABLE IF NOT EXISTS questions (user_id INTEGER, user_name TEXT, question TEXT)')
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
    cursor.execute("SELECT number FROM tickets WHERE number NOT IN (SELECT ticket FROM users) ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- ባለቤት (Admin) ትዕዛዞች ---
async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    conn = sqlite3.connect('lottery.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, phone, ticket, car FROM users")
    users = cursor.fetchall()
    conn.close()
    if not users:
        await update.message.reply_text("እስካሁን የተመዘገበ ሰው የለም።")
        return
    msg = "📋 **የተመዘገቡ ሰዎች ዝርዝር፦**\n\n"
    for u in users:
        msg += f"👤 ስም፦ {u[0]}\n📞 ስልክ፦ {u[1]}\n🎫 ቲኬት፦ {u[2]}\n🚗 መኪና፦ {u[3]}\n---\n"
    await update.message.reply_text(msg)

# --- ጥያቄ ለመቀበል ---
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("እባክዎ ጥያቄዎን እዚህ ይጻፉልን፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return QUESTION

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_text = update.message.text
    if q_text == "⬅️ ተመለስ": return await start(update, context)
    user_id, user_name = update.effective_user.id, update.effective_user.full_name
    conn = sqlite3.connect('lottery.db')
    conn.execute("INSERT INTO questions (user_id, user_name, question) VALUES (?, ?, ?)", (user_id, user_name, q_text))
    conn.commit()
    conn.close()
    await context.bot.send_message(chat_id=OWNER_ID, text=f"📩 አዲስ ጥያቄ ከ {user_name}፦\n\n{q_text}")
    await update.message.reply_text("ጥያቄዎ ደርሶናል። እናመሰግናለን!")
    return ConversationHandler.END

# --- የሎተሪ ምዝገባ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("እንኳን ደህና መጡ ባለቤት! ዝርዝር ለማየት /view_users ይጠቀሙ።")
    await update.message.reply_text("እንኳን ደህና መጡ እጣ ለመቁረጥ ከታች ያለውን ቁልፍ ይጫኑ")
    kb = [["Sino", "Isuzu"], ["Toyota"], ["❓ ጥያቄ ለመጠየቅ"]]
    await update.message.reply_text("እባክዎ መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car = update.message.text
    if car == "❓ ጥያቄ ለመጠየቅ": return await ask_question(update, context)
    if car not in PRICES: return CAR_SELECTION
    context.user_data['car'] = car
    await update.message.reply_text(f"የመረጡት፦ {car}\nዋጋ፦ {PRICES[car]}\n\nአሁን ሙሉ ስምዎን (ባለ 3 ቃል) ያስገቡ፦", 
                                   reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "⬅️ ተመለስ": return await start(update, context)
    if len(text.split()) < 3:
        await update.message.reply_text("እባክዎ ስምዎን በትክክል ባለ 3 ቃል ያስገቡ፦")
        return NAME
    context.user_data['name'] = text
    await update.message.reply_text("አሁን ስልክ ቁጥርዎን ያስገቡ (10 አሃዝ)፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "⬅️ ተመለስ":
        await update.message.reply_text("ስምዎን (ባለ 3 ቃል) ያስገቡ፦")
        return NAME
    if not (text.startswith('0') and len(text) == 10 and text.isdigit()):
        await update.message.reply_text("እባክዎ በትክክል 10 አሃዝ ያለው ስልክ ቁጥር ያስገቡ፦")
        return PHONE
    context.user_data['phone'] = text
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦",
                                   reply_markup=ReplyKeyboardMarkup([["Telebirr", "CBE"], ["⬅️ ተመለስ"]], resize_keyboard=True))
    return PAYMENT_METHOD

async def payment_method_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "⬅️ ተመለስ":
        await update.message.reply_text("ስልክ ቁጥርዎን ያስገቡ፦")
        return PHONE
    if text not in PAYMENT_INFO: return PAYMENT_METHOD
    context.user_data['payment'] = text
    await update.message.reply_text(f"የመረጡት፦ {text}\n{PAYMENT_INFO[text]}\n\nክፍያውን ፈጽመው ስክሪንሾት (Screenshot) እዚህ ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ticket = get_available_ticket()
        if not ticket:
            await update.message.reply_text("ይቅርታ፣ ሁሉም ቲኬቶች አልቀዋል!")
            return ConversationHandler.END
        file_id = update.message.photo[-1].file_id
        d = context.user_data
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT INTO users (car, name, phone, ticket, payment, proof) VALUES (?, ?, ?, ?, ?, ?)",
                     (d['car'], d['name'], d['phone'], ticket, d['payment'], file_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ ክፍያዎ እንደተረጋገጠ የእጣ ቁጥሮ ይደርስዎታል\n\nየእርስዎ ቲኬት ቁጥር፦ {ticket}\nስም፦ {d['name']}\n\nመልካም እድል ይሁንሎ!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("እባክዎ የክፍያ ማረጋገጫ ፎቶ (Screenshot) ይላኩ።")
        return SCREENSHOT

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("view_users", view_users))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CAR_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_method_chosen)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
