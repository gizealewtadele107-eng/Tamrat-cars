import os
import sqlite3
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- Render እንዳይዘጋ የሚያደርግ ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- የቦቱ ቅንብሮች ---
TOKEN = "8466476114:AAEQqcA0r6LcwsBKTZuZxdZRfM2qmFDViSE"
CAR_SELECTION, NAME, PHONE, SCREENSHOT = range(4)

# የመኪና ዓይነቶች እና ዋጋቸው
CARS = {
    "Sino (2000 ETB)": 2000,
    "Isuzu (1500 ETB)": 1500,
    "Toyota (1000 ETB)": 1000
}

# ዳታቤዝ መፍጠሪያ
def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS participants 
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, car TEXT, name TEXT, phone TEXT, screenshot_id TEXT)''')
    conn.close()

# --- የቦቱ ተግባራት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Sino (2000 ETB)", "Isuzu (1500 ETB)"], ["Toyota (1000 ETB)"]]
    await update.message.reply_text(
        "እንኳን ወደ መኪና ዕጣ ቦት በሰላም መጡ! 🚗\nእባክዎ መሳተፍ የሚፈልጉበትን የመኪና ዓይነት ይምረጡ፦",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CAR_SELECTION

async def car_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['car'] = update.message.text
    await update.message.reply_text(f"{update.message.text} መርጠዋል። አሁን ሙሉ ስምዎን ያስገቡ፦")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("አሁን ስልክ ቁጥርዎን ያስገቡ፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    selected
