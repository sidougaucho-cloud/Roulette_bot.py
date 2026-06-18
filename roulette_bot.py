import telebot
import random
import time
import json
import os
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "casino_data.json"
RIGGED_MODE = True
SPIN_GIF = "https://media.giphy.com/media/3o7aDgf7a9Q5cJ4qM0/giphy.gif"

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

# ====================== CLAVIERS ======================
def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🎰 Placer Jetons", callback_data="bet_menu"),
               InlineKeyboardButton("🔄 Tourner la Roue", callback_data="spin_now"))
    markup.add(InlineKeyboardButton("🏆 Classement", callback_data="leaderboard"),
               InlineKeyboardButton("💰 Mon Solde", callback_data="balance"))
    return markup

def bet_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    amounts = [50, 100, 250, 500]
    simple = ["rouge", "noir", "pair", "impair", "manque", "passe"]
    for t in simple:
        for a in amounts:
            markup.add(InlineKeyboardButton(f"{t.capitalize()} {a}", callback_data=f"bet_{t}_{a}"))
    markup.row(
        InlineKeyboardButton("Colonne 1 50", callback_data="bet_col1_50"),
        InlineKeyboardButton("Colonne 2 50", callback_data="bet_col2_50"),
        InlineKeyboardButton("Colonne 3 50", callback_data="bet_col3_50")
    )
    markup.row(
        InlineKeyboardButton("Douzaine 1 50", callback_data="bet_douz1_50"),
        InlineKeyboardButton("Douzaine 2 50", callback_data="bet_douz2_50"),
        InlineKeyboardButton("Douzaine 3 50", callback_data="bet_douz3_50")
    )
    markup.add(InlineKeyboardButton("🔢 Plein (Numéro)", callback_data="bet_number"))
    return markup

# ====================== SPIN ======================
def do_spin(chat_id):
    bets = data["current_round"].get("bets", [])
    if not bets:
        bot.send_message(chat_id, "❌ Aucune mise sur la table.")
        return

    bot.send_animation(chat_id, SPIN_GIF, caption="🎡 **Le croupier lance la roulette...**")

    time.sleep(4)

    result = random.randint(0, 36) if not RIGGED_MODE else choose_smart_result(bets)  # Garde ton système anti-perte
    color = get_color(result)
    text = f"🎰 **Numéro sorti : {result} {color}**\n\n"

    for bet in bets:
        win = calculate_win(bet["type"], result, bet["amount"])
        user = get_user(bet["user_id"])
        if win > 0:
            user["balance"] += win
            text += f"✅ {bet['username']} gagne **{win}** crédits !\n"
        else:
            text += f"❌ {bet['username']} perd sa mise sur {bet['type']}\n"
        try:
            bot.send_message(bet["user_id"], f"Résultat : {result} {color}\nMise {bet['amount']} sur {bet['type']} → {win}")
        except:
            pass

    data["current_round"] = {"bets": [], "active": False}
    save_data(data)
    bot.send_message(chat_id, text + "\n🎲 Prochain tour ouvert.", reply_markup=main_keyboard())

def calculate_win(btype, result, amount):
    if btype in ["rouge", "noir"] and btype in get_color(result).lower():
        return amount * 2
    if btype in ["pair", "impair", "manque", "passe"] and check_simple(btype, result):
        return amount * 2
    if btype.startswith(("col", "douz")) and check_col_douz(btype, result):
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

def choose_smart_result(bets):
    # Ton système anti-perte maison (inchangé)
    total = sum(b["amount"] for b in bets)
    best = []
    min_loss = float('inf')
    for cand in range(37):
        payout = sum(calculate_win(b["type"], cand, b["amount"]) for b in bets)
        profit = total - payout
        if profit >= 0:
            if profit < min_loss:
                min_loss = profit
                best = [cand]
            elif profit == min_loss:
                best.append(cand)
    return random.choice(best) if best else random.randint(0, 36)

# ====================== COMMANDES ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
"""🌟 **Bienvenue au Casino Royale Français** 🌟

Vous êtes à la table de **Roulette Européenne**.
Le croupier vous salue.

💰 Solde : 1000 crédits

Utilisez les boutons pour placer vos jetons comme dans un vrai casino.""", 
        reply_markup=main_keyboard())

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id,
"""🎲 **Règles de la Roulette Française**

**Mises simples (paiement x2)** :
• Rouge / Noir
• Pair / Impair
• Manque (1-18) / Passe (19-36)

**Mises x3** :
• Colonne 1-3
• Douzaine 1-3

**Plein (x36)** : `/bet_numéro 17 100`

Placez vos jetons avec les boutons ci-dessous. Bonne chance !""", reply_markup=bet_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user = get_user(call.from_user.id)

    if call.data == "bet_menu":
        bot.send_message(chat_id, "🪙 **Placez vos jetons sur la table** :", reply_markup=bet_keyboard())
    elif call.data == "spin_now":
        do_spin(chat_id)
    elif call.data == "leaderboard":
        show_leaderboard(chat_id)
    elif call.data == "balance":
        bot.send_message(chat_id, f"💰 **Votre solde** : **{user['balance']} crédits**")

def show_leaderboard(chat_id):
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 **Classement du Casino**\n\n"
    for i, (_, u) in enumerate(sorted_users, 1):
        text += f"{i}. **{u['balance']}** crédits\n"
    bot.send_message(chat_id, text)

@bot.message_handler(commands=['bet_numéro'])
def bet_number(message):
    try:
        _, num, amt = message.text.split()
        num = int(num)
        amt = int(amt)
        user = get_user(message.from_user.id)
        if amt > user["balance"] or not 0 <= num <= 36:
            bot.reply_to(message, "❌ Numéro invalide (0-36) ou solde insuffisant.")
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
        bot.reply_to(message, f"🪙 **Jeton placé** sur le **plein {num}** ({amt} crédits)")
    except:
        bot.reply_to(message, "Usage : `/bet_numéro 17 100`")

print("🚀 Casino Français Prêt !")
bot.infinity_polling()
