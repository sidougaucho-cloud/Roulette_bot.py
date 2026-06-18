import telebot
import random
import time
import json
import os
import threading
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "casino_data.json"
RIGGED_MODE = True

# GIF Animation Roulette
SPIN_GIF = "https://media.giphy.com/media/3o7aDgf7a9Q5cJ4qM0/giphy.gif"  # Roulette qui tourne

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "current_round": {"bets": [], "active": False}, "history": [], "jackpot": 15000}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

def get_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 1000, "history": []}
    return data["users"][uid]

def get_color(n):
    if n == 0: return "🟢 Vert"
    reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    return "🔴 Rouge" if n in reds else "⚫ Noir"

# Claviers
def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🎰 Miser", callback_data="bet_menu"),
               InlineKeyboardButton("🔄 Spin", callback_data="spin_now"))
    markup.add(InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
               InlineKeyboardButton("💰 Balance", callback_data="balance"))
    return markup

def bet_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    amounts = [50, 100, 250, 500]
    simple = ["rouge", "noir", "pair", "impair", "manque", "passe"]
    for t in simple:
        for a in amounts:
            markup.add(InlineKeyboardButton(f"{t.capitalize()} {a}", callback_data=f"bet_{t}_{a}"))
    markup.row(
        InlineKeyboardButton("Col1 50", callback_data="bet_col1_50"),
        InlineKeyboardButton("Col2 50", callback_data="bet_col2_50"),
        InlineKeyboardButton("Col3 50", callback_data="bet_col3_50")
    )
    markup.row(
        InlineKeyboardButton("Douz1 50", callback_data="bet_douz1_50"),
        InlineKeyboardButton("Douz2 50", callback_data="bet_douz2_50"),
        InlineKeyboardButton("Douz3 50", callback_data="bet_douz3_50")
    )
    markup.add(InlineKeyboardButton("🔢 Numéro précis", callback_data="bet_number"))
    return markup

# ====================== FONCTIONS PRINCIPALES ======================
def choose_smart_result(bets):
    total_bets = sum(b["amount"] for b in bets)
    best = []
    min_loss = float('inf')
    for candidate in range(37):
        payout = 0
        for bet in bets:
            win = 0
            btype = bet["type"]
            if btype in ["rouge", "noir"] and btype in get_color(candidate).lower():
                win = bet["amount"] * 2
            elif btype in ["pair","impair","manque","passe"] and check_simple(btype, candidate):
                win = bet["amount"] * 2
            elif btype.startswith(("col","douz")) and check_col_douz(btype, candidate):
                win = bet["amount"] * 3
            elif btype.isdigit() and int(btype) == candidate:
                win = bet["amount"] * 36
            payout += win
        profit = total_bets - payout
        if profit >= 0 and profit <= min_loss:
            if profit < min_loss:
                best = [candidate]
                min_loss = profit
            else:
                best.append(candidate)
    return random.choice(best) if best else random.randint(0, 36)

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

# ====================== SPIN AVEC ANIMATION ======================
def do_spin(chat_id):
    if data["current_round"].get("timer"):
        data["current_round"]["timer"].cancel()
    bets = data["current_round"].get("bets", [])
    if not bets:
        bot.send_message(chat_id, "❌ Aucune mise pour le moment.")
        return

    # Animation GIF
    bot.send_animation(chat_id, SPIN_GIF, caption="🎡 **La roulette tourne...**")

    time.sleep(4)  # Temps de l'animation

    result = choose_smart_result(bets) if RIGGED_MODE else random.randint(0, 36)
    color = get_color(result)
    result_text = f"🎰 **Résultat : {result} {color}** (Maison protégée)\n\n"

    total_payout = 0
    for bet in bets:
        u = get_user(bet["user_id"])
        win = 0
        btype = bet["type"]
        if btype in ["rouge", "noir"] and btype in color.lower():
            win = bet["amount"] * 2
        elif btype in ["pair","impair","manque","passe"] and check_simple(btype, result):
            win = bet["amount"] * 2
        elif btype.startswith(("col","douz")) and check_col_douz(btype, result):
            win = bet["amount"] * 3
        elif btype.isdigit() and int(btype) == result:
            win = bet["amount"] * 36

        if win > 0:
            u["balance"] += win
            total_payout += win
            result_text += f"✅ {bet['username']} → +{win}\n"
        else:
            result_text += f"❌ {bet['username']} → {bet['amount']} sur {btype}\n"

        try:
            bot.send_message(bet["user_id"], f"🎰 Résultat : {result} {color}\nTa mise {bet['amount']} sur {btype} → {'+'+str(win) if win else '0'}")
        except:
            pass

    house = sum(b["amount"] for b in bets) - total_payout
    result_text += f"\n💰 Maison : +{house} crédits"

    data["current_round"] = {"bets": [], "active": False}
    save_data(data)
    bot.send_message(chat_id, result_text + "\n🎲 Prochaine ronde !", reply_markup=bet_keyboard())

# ====================== COMMANDES ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🎰 **Casino Roulette Royale**\nTable multijoueur ouverte !", reply_markup=main_keyboard())

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, """🎲 **Guide des Mises**

**x2** : Rouge / Noir / Pair / Impair / Manque (1-18) / Passe (19-36)
**x3** : Colonne 1-3 / Douzaine 1-3
**x36** : Numéro précis → `/bet_numéro 17 100`

Utilise les boutons ci-dessous !""", reply_markup=bet_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user = get_user(call.from_user.id)
    chat_id = call.message.chat.id

    if call.data == "bet_menu":
        bot.send_message(chat_id, "🎲 Choisis ta mise :", reply_markup=bet_keyboard())
    elif call.data == "spin_now":
        do_spin(chat_id)
    elif call.data == "leaderboard":
        show_leaderboard(chat_id)
    elif call.data == "balance":
        bot.send_message(chat_id, f"💰 **Ton solde : {user['balance']} crédits**")

def show_leaderboard(chat_id):
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 **Leaderboard**\n\n"
    for i, (_, u) in enumerate(sorted_users, 1):
        text += f"{i}. **{u['balance']}** crédits\n"
    bot.send_message(chat_id, text)

@bot.message_handler(commands=['bet_numéro'])
def bet_number(message):
    try:
        _, num, amt = message.text.split()
        num, amt = int(num), int(amt)
        user = get_user(message.from_user.id)
        if amt > user["balance"] or not 0 <= num <= 36:
            bot.reply_to(message, "❌ Montant trop élevé ou numéro invalide (0-36)")
            return
        user["balance"] -= amt
        if not data["current_round"]["active"]:
            data["current_round"]["active"] = True
            data["current_round"]["bets"] = []
        data["current_round"]["bets"].append({
            "user_id": message.from_user.id,
            "username": message.from_user.first_name,
            "type": str(num),
            "amount": amt
        })
        save_data(data)
        bot.reply_to(message, f"✅ Mise de **{amt}** sur le numéro **{num}** enregistrée !")
    except:
        bot.reply_to(message, "Usage : `/bet_numéro 17 100`")

@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    bot.reply_to(message, "💸 **Demande de retrait**\n\nContacte l'admin pour retirer tes crédits :\n@tonusername\n\nIndique ton montant et ta méthode (PayPal / Crypto).")

print("🚀 Bot Roulette Final - Animation + Retrait activé !")
bot.infinity_polling()
