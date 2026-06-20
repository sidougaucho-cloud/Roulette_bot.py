import telebot
import random
import time
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "casino_data.json"
WELCOME_IMAGE = "https://i.postimg.cc/7ZSb4wnv/BC5238CA-BA84-46EC-9A68-5525C7137EFD.png"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "current_round": {"bets": [], "active": False}}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

def get_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 10000 if user_id == ADMIN_ID else 0}
    return data["users"][uid]

def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("🎰 Jouez !", callback_data="bet_menu"),
        InlineKeyboardButton("💰 Solde", callback_data="balance"),
        InlineKeyboardButton("📥 Recharger", callback_data="deposit")
    )
    markup.add(
        InlineKeyboardButton("📤 Encaisser", callback_data="withdraw"),
        InlineKeyboardButton("🆘 SAV", callback_data="help")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_photo(
        message.chat.id, 
        WELCOME_IMAGE, 
        caption="""🌟 **PATOUCH CASINO** 🌟

Bienvenue dans le casino le plus prestigieux !

Choisissez une option ci-dessous :""", 
        reply_markup=main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "bet_menu":
        bot.send_message(chat_id, "🪙 Menu des mises (en cours de développement)")
    elif call.data == "balance":
        bot.send_message(chat_id, "💰 Solde (en cours de développement)")
    elif call.data == "deposit":
        bot.send_message(chat_id, "📥 Recharge : Envoyez le montant et la méthode (PayPal / Crypto)")
    elif call.data == "withdraw":
        bot.send_message(chat_id, "📤 Encaisser : Envoyez le montant et votre nom PayPal")
    elif call.data == "help":
        bot.send_message(chat_id, "🆘 Contactez l'admin pour toute aide.")

print("🚀 PATOUCH Casino démarré avec succès")
bot.infinity_polling()
