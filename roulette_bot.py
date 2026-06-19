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
RIGGED_MODE = True
TABLE_IMAGE = "https://i.imgur.com/8Z2vK8J.jpg"   # Table de roulette

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
        data["users"][uid] = {"balance": 10000 if user_id == ADMIN_ID else 0, "history": []}
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
    markup.add(InlineKeyboardButton("🏆 Classement", callback_data="leaderboard"),
               InlineKeyboardButton("💰 Solde", callback_data="balance"))
    return markup

def bet_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🔴 Rouge", callback_data="bet_rouge_100"),
               InlineKeyboardButton("⚫ Noir", callback_data="bet_noir_100"))
    markup.add(InlineKeyboardButton("Pair", callback_data="bet_pair_100"),
               InlineKeyboardButton("Impair", callback_data="bet_impair_100"))
    markup.add(InlineKeyboardButton("Manque", callback_data="bet_manque_100"),
               InlineKeyboardButton("Passe", callback_data="bet_passe_100"))
    markup.add(InlineKeyboardButton("Colonnes & Douzaines", callback_data="theme_col"))
    markup.add(InlineKeyboardButton("🔢 Numéro", callback_data="choose_number"))
    markup.add(InlineKeyboardButton("⬅️ Retour", callback_data="back_main"))
    return markup

# ====================== CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user = get_user(call.from_user.id)

    if call.data == "bet_menu":
        bot.send_photo(chat_id, TABLE_IMAGE, caption="🪙 **Table PATOUCH** - Placez vos jetons", reply_markup=bet_keyboard())
    elif call.data == "back_main":
        bot.send_message(chat_id, "Retour au menu", reply_markup=main_keyboard())
    elif call.data == "choose_number":
        bot.send_message(chat_id, "🔢 Entrez : `numéro montant`\nExemple : `17 100`")
    elif call.data.startswith("bet_"):
        handle_bet(call, user, chat_id)
    elif call.data == "spin_now":
        do_spin(chat_id)
    elif call.data == "balance":
        bot.send_message(chat_id, f"💰 Solde : **{user['balance']}** crédits")
    elif call.data == "leaderboard":
        show_leaderboard(chat_id)

def handle_bet(call, user, chat_id):
    try:
        _, btype, amount_str = call.data.split("_")
        amount = int(amount_str)
        if user["balance"] < amount:
            bot.answer_callback_query(call.id, "❌ Solde insuffisant", show_alert=True)
            return
        user["balance"] -= amount
        if not data["current_round"]["active"]:
            data["current_round"] = {"bets": [], "active": True}
        data["current_round"]["bets"].append({
            "user_id": call.from_user.id,
            "username": call.from_user.first_name,
            "type": btype,
            "amount": amount
        })
        save_data()
        bot.answer_callback_query(call.id, f"✅ {amount} sur {btype}")
        show_current_bets(chat_id)
    except:
        bot.answer_callback_query(call.id, "Erreur")

def show_current_bets(chat_id):
    bets = data["current_round"].get("bets", [])
    text = "📋 **Mises en cours :**\n"
    for b in bets:
        text += f"• {b['username']} : {b['amount']} sur {b['type']}\n"
    bot.send_message(chat_id, text)

def do_spin(chat_id):
    bets = data["current_round"].get("bets", [])
    if not bets:
        bot.send_message(chat_id, "Aucune mise.")
        return
    bot.send_animation(chat_id, "https://media.giphy.com/media/3o7aDgf7a9Q5cJ4qM0/giphy.gif", caption="🎡 La roulette tourne...")
    time.sleep(4)
    result = random.randint(0, 36)
    color = get_color(result)
    text = f"🎰 Résultat : {result} {color}\n\n"
    for bet in bets:
        win = 0
        # Calcul simple des gains...
        if bet["type"] in ["rouge", "noir"] and bet["type"] in color.lower():
            win = bet["amount"] * 2
        # ... (ajoute le reste si besoin)
        text += f"{bet['username']} : {'+' + str(win) if win else '0'}\n"
    data["current_round"] = {"bets": [], "active": False}
    save_data()
    bot.send_message(chat_id, text, reply_markup=main_keyboard())

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, """🌟 **PATOUCH CASINO** 🌟

Bienvenue dans le casino le plus exclusif !

Utilisez les boutons ci-dessous pour jouer.""", reply_markup=main_keyboard())

print("🚀 PATOUCH Casino lancé")
bot.infinity_polling()
