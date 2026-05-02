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
OWNER_ID = 7705713321  # የእርስዎ ID እዚህ ገብቷል
CAR_SELECTION, NAME, PHONE, PAYMENT_METHOD, SCREENSHOT = range(5)

PRICES = {"Sino": "2000 ETB", "Isuzu": "1500 ETB", "Toyota": "1000 ETB"}
PAYMENT_INFO = {
    "Telebirr": "ቁጥር: 0954873497",
    "CBE": "አካውንት: 1000536009276"
}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT)''')
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
    cursor.execute("SELECT number FROM tickets WHERE number NOT IN (SELECT ticket FROM users) ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- ባለቤት ብቻ የሚያያቸው ትዕዛዞች ---
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

# --- የሎተሪ ምዝገባ ሂደት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("እንኳን ደህና መጡ ባለቤት! የተመዘገቡትን ለማየት /view_users ይጫኑ።")
    await update.message.reply_text("እንኳን ደህና መጡ እጣ ለመቁረጥ ከታች ያለውን ቁልፍ ይጫኑ")
    kb = [["Sino", "Isuzu"], ["Toyota"]]
    await update.message.reply_text("እባክዎ መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car = update.message.text
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
    if text == "⬅️ ተመለስ": return NAME
    if not (text.startswith('0') and
