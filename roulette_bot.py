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
TABLE_IMAGE = "https://i.imgur.com/8Z2vK8J.jpg"

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
    markup.add(InlineKeyboardButton("Manque (1-18)", callback_data="bet_manque_100"),
               InlineKeyboardButton("Passe (19-36)", callback_data="bet_passe_100"))
    markup.add(InlineKeyboardButton("Colonnes", callback_data="col_menu"),
               InlineKeyboardButton("Douzaines", callback_data="douz_menu"))
    markup.add(InlineKeyboardButton("🔢 Numéros Pleins", callback_data="num_menu"))
    markup.add(InlineKeyboardButton("⬅️ Retour Menu", callback_data="back_main"))
    return markup

# ====================== CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user = get_user(user_id)

    if call.data == "bet_menu":
        bot.send_photo(chat_id, TABLE_IMAGE, caption="🪙 **Table PATOUCH** - Placez vos jetons", reply_markup=bet_keyboard())

    elif call.data == "back_main":
        bot.send_message(chat_id, "Retour au menu principal", reply_markup=main_keyboard())

    elif call.data.startswith("bet_"):
        handle_simple_bet(call, user)

    elif call.data == "num_menu":
        show_number_buttons(chat_id)

    elif call.data.startswith("num_"):
        handle_number_bet(call, user, chat_id)

    elif call.data == "balance_menu":
        show_balance_menu(chat_id, user)

    elif call.data == "spin_now":
        do_spin(chat_id)

    elif call.data == "leaderboard":
        show_leaderboard(chat_id)

def handle_simple_bet(call, user):
    try:
        _, btype, amt_str = call.data.split("_")
        amount = int(amt_str)
        if user["balance"] < amount:
            bot.answer_callback_query(call.id, "❌ Solde insuffisant", show_alert=True)
            return
        user["balance"] -= amount
        add_bet(call.from_user.id, call.from_user.first_name, btype, amount)
        bot.answer_callback_query(call.id, f"✅ {amount} sur {btype}")
        show_current_bets(call.message.chat.id)
    except:
        bot.answer_callback_query(call.id, "Erreur")

def show_number_buttons(chat_id):
    markup = InlineKeyboardMarkup(row_width=6)
    for i in range(37):
        markup.add(InlineKeyboardButton(str(i), callback_data=f"num_{i}_100"))
    markup.add(InlineKeyboardButton("⬅️ Retour", callback_data="bet_menu"))
    bot.send_message(chat_id, "🔢 Choisissez un numéro (mise 100 crédits) :", reply_markup=markup)

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

# ====================== SOLDE & OPÉRATIONS ======================
def show_balance_menu(chat_id, user):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("💳 Recharger", callback_data="deposit"),
               InlineKeyboardButton("💸 Encaisser", callback_data="withdraw"))
    markup.add(InlineKeyboardButton("⬅️ Retour", callback_data="back_main"))
    bot.send_message(chat_id, f"💰 **Solde actuel** : **{user['balance']}** crédits\n\nQue voulez-vous faire ?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["deposit", "withdraw"])
def payment_handler(call):
    if call.data == "deposit":
        bot.send_message(call.message.chat.id, "💳 **Recharge**\n\nMontant + méthode (PayPal / Crypto / Liquide)\nExemple : `500 PayPal`")
    else:
        bot.send_message(call.message.chat.id, "💸 **Retrait**\n\nMontant + votre nom PayPal\nExemple : `300 JeanDupont`")

@bot.message_handler(func=lambda m: True)
def handle_payment_message(message):
    text = message.text.lower()
    if "paypal" in text or "crypto" in text or "liquide" in text:
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ **Demande envoyée à l'admin**\nVotre demande sera traitée rapidement.")
    elif any(c.isdigit() for c in text) and ("pay" in text or "@" in text or "paypal" in text):
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ **Demande de retrait envoyée**\nL'admin a été prévenu. Votre demande sera traitée le plus rapidement possible.")

# ====================== SPIN ======================
def do_spin(chat_id):
    bets = data["current_round"].get("bets", [])
    if not bets:
        bot.send_message(chat_id, "❌ Aucune mise.")
        return
    bot.send_animation(chat_id, "https://media.giphy.com/media/3o7aDgf7a9Q5cJ4qM0/giphy.gif", caption="🎡 **La roulette tourne chez PATOUCH...**")
    time.sleep(4)
    result = random.randint(0, 36)
    color = get_color(result)
    text = f"🎰 **Résultat : {result} {color}**\n\n"
    for bet in bets:
        win = calculate_win(bet["type"], result, bet["amount"])
        if win > 0:
            get_user(bet["user_id"])["balance"] += win
            text += f"✅ {bet['username']} gagne **{win}**\n"
        else:
            text += f"❌ {bet['username']} perd\n"
    data["current_round"] = {"bets": [], "active": False}
    save_data()
    bot.send_message(chat_id, text + "\n🎲 Prochain tour ouvert !", reply_markup=main_keyboard())

def calculate_win(btype, result, amount):
    if btype in ["rouge", "noir"] and btype in get_color(result).lower():
        return amount * 2
    if btype in ["pair", "impair", "manque", "passe"] and check_simple(btype, result):
        return amount * 2
    if btype.startswith(("col","douz")) and check_col_douz(btype, result):
        return amount * 3
    if btype.isdigit() and int(btype) == result:
        return amount * 36
    return 0

def check_simple(t, n):
    if t == "pair": return n % 2 == 0 and n != 0
    if t == "impair": return n % 2 == 1
    if t == "manque": return 1 <= n <= 18
    if t == "passe": return 19 <= n <= 36
    return False

def check_col_douz(t, n):
    if t in ["col1","douz1"]: return 1 <= n <= 12
    if t in ["col2","douz2"]: return 13 <= n <= 24
    if t in ["col3","douz3"]: return 25 <= n <= 36
    return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, """🌟 **PATOUCH CASINO** 🌟

Bienvenue dans le casino le plus prestigieux !

Utilisez les boutons pour jouer. Bonne chance !""", reply_markup=main_keyboard())

print("🚀 PATOUCH Casino - Version Stable")
bot.infinity_polling()
