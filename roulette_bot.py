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
TABLE_IMAGE = "https://i.imgur.com/8Z2vK8J.jpg"   # Change si tu veux ta photo

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
        bot.send_photo(chat_id, TABLE_IMAGE, caption="🪙 **Table PATOUCH** - Placez vos jetons", reply_markup=bet_keyboard())

    elif call.data == "back_main":
        bot.send_message(chat_id, "Retour au menu principal", reply_markup=main_keyboard())

    elif call.data == "num_menu":
        show_number_buttons(chat_id)

    elif call.data.startswith("bet_"):
        handle_bet(call, user, chat_id)

    elif call.data.startswith("num_"):
        handle_number_bet(call, user, chat_id)

    elif call.data == "spin_now":
        do_spin(chat_id)

    elif call.data == "balance_menu":
        show_balance_menu(chat_id, user)

    elif call.data == "leaderboard":
        show_leaderboard(chat_id)

def handle_bet(call, user, chat_id):
    try:
        _, btype, amt = call.data.split("_")
        amount = int(amt)
        if user["balance"] < amount:
            bot.answer_callback_query(call.id, "❌ Solde insuffisant", show_alert=True)
            return
        user["balance"] -= amount
        add_bet(call.from_user.id, call.from_user.first_name, btype, amount)
        bot.answer_callback_query(call.id, f"✅ {amount} sur {btype}")
        show_current_bets(chat_id)
    except:
        bot.answer_callback_query(call.id, "Erreur")

def handle_number_bet(call, user, chat_id):
    try:
        _, num, amt = call.data.split("_")
        amount = int(amt)
        if user["balance"] < amount:
            bot.answer_callback_query(call.id, "❌ Solde insuffisant")
            return
        user["balance"] -= amount
        add_bet(call.from_user.id, call.from_user.first_name, num, amount)
        bot.answer_callback_query(call.id, f"✅ Mise sur {num}")
        show_current_bets(chat_id)
    except:
        pass

def show_number_buttons(chat_id):
    markup = InlineKeyboardMarkup(row_width=6)
    for i in range(37):
        markup.add(InlineKeyboardButton(str(i), callback_data=f"num_{i}_100"))
    markup.add(InlineKeyboardButton("⬅️ Retour", callback_data="bet_menu"))
    bot.send_message(chat_id, "🔢 Choisissez un numéro (mise 100 crédits) :", reply_markup=markup)

def add_bet(user_id, username, btype, amount):
    if not data["current_round"]["active"]:
        data["current_round"] = {"bets": [], "active": True}
    data["current_round"]["bets"].append({
        "user_id": user_id,
        "username": username,
        "type": btype,
        "amount": amount
    })
    save_data()

def show_current_bets(chat_id):
    bets = data["current_round"].get("bets", [])
    if not bets: return
    text = "📋 **Mises en cours :**\n\n"
    for b in bets:
        text += f"• {b['username']} : {b['amount']} sur **{b['type']}**\n"
    bot.send_message(chat_id, text)

def do_spin(chat_id):
    bets = data["current_round"].get("bets", [])
    if not bets:
        bot.send_message(chat_id, "❌ Aucune mise.")
        return
    bot.send_animation(chat_id, "https://media.giphy.com/media/3o7aDgf7a9Q5cJ4qM0/giphy.gif", caption="🎡 La roulette tourne...")
    time.sleep(4)
    result = random.randint(0, 36)
    color = get_color(result)
    text = f"🎰 **Résultat : {result} {color}**\n\n"
    for bet in bets:
        win = 0
        if bet["type"] in ["rouge", "noir"] and bet["type"] in color.lower():
            win = bet["amount"] * 2
        elif bet["type"].isdigit() and int(bet["type"]) == result:
            win = bet["amount"] * 36
        text += f"{bet['username']} → {win}\n"
    data["current_round"] = {"bets": [], "active": False}
    save_data()
    bot.send_message(chat_id, text + "\n🎲 Prochain tour ouvert.", reply_markup=main_keyboard())

def show_balance_menu(chat_id, user):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("💳 Recharger", callback_data="deposit"),
               InlineKeyboardButton("💸 Encaisser", callback_data="withdraw"))
    bot.send_message(chat_id, f"💰 **Solde actuel** : **{user['balance']}** crédits", reply_markup=markup)

def show_leaderboard(chat_id):
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 **Classement PATOUCH**\n\n"
    for i, (_, u) in enumerate(sorted_users, 1):
        text += f"{i}. **{u['balance']}** crédits\n"
    bot.send_message(chat_id, text)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_photo(message.chat.id, TABLE_IMAGE, caption="""🌟 **PATOUCH CASINO** 🌟

Bienvenue sur la table de roulette !

Utilisez les boutons ci-dessous.""", reply_markup=main_keyboard())

print("🚀 PATOUCH Casino démarré avec succès")
bot.infinity_polling()
