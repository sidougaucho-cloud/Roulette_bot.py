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

# ✅ Ta photo pour le menu principal
MAIN_IMAGE = "https://i.imgur.com/YOUR_IMAGE_LINK.jpg"  # ← Tu dois uploader ta photo et mettre le lien ici

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

def get_color(n):
    if n == 0: return "🟢 Vert"
    reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    return "🔴 Rouge" if n in reds else "⚫ Noir"

# ====================== CLAVIERS ======================
def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🪙 Placer Jetons", callback_data="bet_menu"),
               InlineKeyboardButton("🎡 Tourner la Roue", callback_data="spin_now"))
    markup.add(InlineKeyboardButton("💰 Solde & Opérations", callback_data="balance_menu"),
               InlineKeyboardButton("🏆 Classement", callback_data="leaderboard"))
    return markup

def bet_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🔴 Rouge", callback_data="bet_rouge_100"),
               InlineKeyboardButton("⚫ Noir", callback_data="bet_noir_100"))
    markup.add(InlineKeyboardButton("Pair", callback_data="bet_pair_100"),
               InlineKeyboardButton("Impair", callback_data="bet_impair_100"))
    markup.add(InlineKeyboardButton("Manque", callback_data="bet_manque_100"),
               InlineKeyboardButton("Passe", callback_data="bet_passe_100"))
    markup.add(InlineKeyboardButton("🔢 Numéros", callback_data="num_menu"))
    markup.add(InlineKeyboardButton("⬅️ Retour", callback_data="back_main"))
    return markup

# ====================== CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user = get_user(call.from_user.id)

    if call.data == "bet_menu":
        bot.send_photo(chat_id, TABLE_IMAGE, caption="🪙 **Table de Roulette PATOUCH**", reply_markup=bet_keyboard())
    elif call.data == "back_main":
        bot.send_message(chat_id, "Retour au menu", reply_markup=main_keyboard())
    elif call.data == "num_menu":
        show_number_buttons(chat_id)
    elif call.data.startswith("bet_"):
        handle_bet(call, user, chat_id)
    elif call.data == "spin_now":
        do_spin(chat_id)
    elif call.data == "balance_menu":
        show_balance_menu(chat_id, user)
    elif call.data == "leaderboard":
        show_leaderboard(chat_id)

# ... (le reste du code est le même que la version précédente, stable)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_photo(message.chat.id, MAIN_IMAGE, caption="""🌟 **PATOUCHROULETTE** 🌟

Bienvenue dans le casino le plus chaud de Telegram !

Utilisez les boutons ci-dessous pour jouer.""", reply_markup=main_keyboard())

print("🚀 PATOUCHROULETTE démarré")
bot.infinity_polling()
