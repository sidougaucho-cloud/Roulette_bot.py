import telebot
import random
import time
import json
import os
import threading
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configuration via variables d'environnement (sécurisé)
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

if not TOKEN or ADMIN_ID == 0:
    raise ValueError("TOKEN et ADMIN_ID doivent être définis dans les variables d'environnement")

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "casino_data.json"
RIGGED_MODE = True  # Maison protégée par défaut

# Chargement des données
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},
        "current_round": {"bets": [], "active": False},
        "history": [],
        "jackpot": 15000
    }

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

# ====================== CLAVIERS ======================
def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎰 Miser", callback_data="bet_menu"),
        InlineKeyboardButton("🔄 Spin", callback_data="spin_now")
    )
    markup.add(
        InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
        InlineKeyboardButton("💰 Balance", callback_data="balance")
    )
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

# Timer automatique
def start_auto_timer(chat_id):
    if data["current_round"].get("timer"):
        data["current_round"]["timer"].cancel()
    timer = threading.Timer(60.0, lambda: auto_spin(chat_id))
    timer.start()
    data["current_round"]["timer"] = timer

def auto_spin(chat_id):
    if data["current_round"]["bets"]:
        bot.send_message(chat_id, "⏰ Temps écoulé ! La roulette tourne...")
        do_spin(chat_id)

# Analyse intelligente (maison ne perd jamais)
def choose_smart_result(bets):
    total_bets = sum(bet["amount"] for bet in bets)
    best_results = []
    min_loss = float('inf')

    for candidate in range(37):
        payout = 0
        for bet in bets:
            win_amount = 0
            btype = bet["type"]
            if btype in ["rouge", "noir"] and btype in get_color(candidate).lower():
                win_amount = bet["amount"] * 2
            elif btype in ["pair","impair","manque","passe"] and check_simple(btype, candidate):
                win_amount = bet["amount"] * 2
            elif btype.startswith(("col","douz")) and check_col_douz(btype, candidate):
                win_amount = bet["amount"] * 3
            elif btype.isdigit() and int(btype) == candidate:
                win_amount = bet["amount"] * 36
            payout += win_amount

        house_profit = total_bets - payout
        if house_profit >= 0:
            if house_profit < min_loss:
                min_loss = house_profit
                best_results = [candidate]
            elif house_profit == min_loss:
                best_results.append(candidate)

    return random.choice(best_results) if best_results else random.randint(0, 36)

# ====================== CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user = get_user(user_id)

    if call.data == "bet_menu":
        bot.send_message(chat_id, "🎲 Choisis ta mise :", reply_markup=bet_keyboard())
    elif call.data == "spin_now":
        do_spin(chat_id)
    elif call.data == "leaderboard":
        show_leaderboard(chat_id)
    elif call.data == "balance":
        bot.answer_callback_query(call.id, f"💰 {user['balance']} crédits")
    elif call.data.startswith("bet_"):
        handle_bet(call, user, chat_id)

def handle_bet(call, user, chat_id):
    try:
        parts = call.data.split("_")
        btype = parts[1]
        amount = int(parts[2])
        if user["balance"] < amount:
            bot.answer_callback_query(call.id, "❌ Solde insuffisant", show_alert=True)
            return
        user["balance"] -= amount

        if not data["current_round"]["active"]:
            data["current_round"]["active"] = True
            data["current_round"]["bets"] = []
            start_auto_timer(chat_id)

        data["current_round"]["bets"].append({
            "user_id": call.from_user.id,
            "username": call.from_user.first_name,
            "type": btype,
            "amount": amount
        })
        save_data(data)
        bot.answer_callback_query(call.id, f"✅ Mise {amount} sur {btype}")
        bot.send_message(chat_id, f"👤 {call.from_user.first_name} mise **{amount}** sur **{btype}**", reply_markup=bet_keyboard())
    except:
        pass

# ====================== SPIN ======================
def do_spin(chat_id):
    if data["current_round"].get("timer"):
        data["current_round"]["timer"].cancel()

    bets = data["current_round"]["bets"]
    if not bets:
        bot.send_message(chat_id, "❌ Aucune mise.")
        return

    bot.send_message(chat_id, "🎡 Analyse des mises et rotation...")

    time.sleep(3)

    result = choose_smart_result(bets) if RIGGED_MODE else random.randint(0, 36)
    color = get_color(result)
    result_text = f"🎰 **Résultat : {result} {color}** (Contrôlé)\n\n"

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
            result_text += f"✅ {bet['username']} +{win}\n"
        else:
            result_text += f"❌ {bet['username']} {bet['amount']} sur {btype}\n"

        try:
            bot.send_message(bet["user_id"], f"🎰 {result} {color}\nTa mise sur {btype} → {'+'+str(win) if win else '0'}")
        except:
            pass

    house_profit = sum(b["amount"] for b in bets) - total_payout
    result_text += f"\n💰 Maison : +{house_profit} ce spin"

    data["current_round"] = {"bets": [], "active": False}
    save_data(data)

    bot.send_message(chat_id, result_text + "\n🎲 Prochaine ronde !", reply_markup=bet_keyboard())

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

# ====================== COMMANDES ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🎰 **Casino Roulette Royale** - Table ouverte !\nUtilise les boutons.", reply_markup=main_keyboard())

@bot.message_handler(commands=['bet_numéro'])
def bet_number(message):
    try:
        _, num, amt = message.text.split()
        num, amt = int(num), int(amt)
        user = get_user(message.from_user.id)
        if user["balance"] < amt or not 0 <= num <= 36:
            bot.reply_to(message, "❌ Valeur invalide")
            return
        user["balance"] -= amt
        if not data["current_round"]["active"]:
            data["current_round"]["active"] = True
            data["current_round"]["bets"] = []
            start_auto_timer(message.chat.id)
        data["current_round"]["bets"].append({
            "user_id": message.from_user.id,
            "username": message.from_user.first_name,
            "type": str(num),
            "amount": amt
        })
        save_data(data)
        bot.reply_to(message, f"✅ Mise {amt} sur **{num}**")
    except:
        bot.reply_to(message, "Usage : `/bet_numéro 17 100`")

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 **Leaderboard**\n\n"
    for i, (_, u) in enumerate(sorted_users, 1):
        text += f"{i}. Joueur — **{u['balance']}** crédits\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['deposit'])
def deposit(message):
    bot.reply_to(message, "💳 Rechargement (PayPal / Crypto / Meet-up) → Contacte l'admin")

# Commandes Admin
@bot.message_handler(commands=['force'])
def force_result(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        global FORCED_RESULT
        FORCED_RESULT = int(message.text.split()[1])
        bot.reply_to(message, f"✅ Prochain spin forcé sur {FORCED_RESULT}")
    except:
        bot.reply_to(message, "Usage : /force 17")

@bot.message_handler(commands=['rigged'])
def toggle_rigged(message):
    if message.from_user.id != ADMIN_ID: return
    global RIGGED_MODE
    RIGGED_MODE = not RIGGED_MODE
    bot.reply_to(message, f"Mode Rigged : {'✅ ON' if RIGGED_MODE else '❌ OFF'}")

print("🚀 Bot Roulette Casino démarré !")
bot.infinity_polling()
