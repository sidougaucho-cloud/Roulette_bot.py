import telebot
from telebot import types
from collections import defaultdict
import os
import json

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYPAL_USERNAME = os.getenv("PAYPAL_USERNAME")

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN manquant dans les variables Railway")

bot = telebot.TeleBot(TOKEN)

# ==================== STOCK ====================
STOCK_FILE = "stock.json"

def load_stock():
    try:
        with open(STOCK_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Création du stock par défaut
        default_stock = {}
        for cat, items in products.items():
            default_stock[cat] = {item["name"]: 10 for item in items}
        save_stock(default_stock)
        return default_stock

def save_stock(stock_data):
    try:
        with open(STOCK_FILE, "w") as f:
            json.dump(stock_data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde stock: {e}")

# ==================== PRODUITS ====================
products = {
    "otacos": [
        {"name": "Tacos Classique", "price": 8.90},
        {"name": "Tacos Poulet", "price": 9.90},
        {"name": "Frites", "price": 3.50},
    ],
    "pizzatime": [
        {"name": "Margherita", "price": 10.90},
        {"name": "Pepperoni", "price": 12.90},
        {"name": "Boisson", "price": 2.50},
    ],
    "chamas": [
        {"name": "Burrito Boeuf", "price": 9.50},
        {"name": "Quesadilla", "price": 8.90},
    ],
    "pitaya": [
        {"name": "Açaï Bowl", "price": 7.90},
        {"name": "Smoothie", "price": 5.90},
    ],
    "divers": [
        {"name": "Hot Dog", "price": 4.50},
        {"name": "Croissant", "price": 2.20},
    ],
    "traidinn": [
        {"name": "Burger Classique", "price": 11.90},
        {"name": "Chicken Burger", "price": 10.90},
    ]
}

stock = load_stock()
carts = defaultdict(dict)

# ==================== MENUS ====================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Nos produits", callback_data="menu_produits"),
        types.InlineKeyboardButton("💰 Recharger", callback_data="menu_recharger")
    )
    return markup

def produits_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌮 O’Tacos", callback_data="cat_otacos"),
        types.InlineKeyboardButton("🍕 Pizza Time", callback_data="cat_pizzatime"),
        types.InlineKeyboardButton("🌯 Chamas Tacos", callback_data="cat_chamas"),
        types.InlineKeyboardButton("🥑 Pitaya", callback_data="cat_pitaya"),
        types.InlineKeyboardButton("🍟 Divers Snack", callback_data="cat_divers"),
        types.InlineKeyboardButton("🍔 Traidinn", callback_data="cat_traidinn")
    )
    markup.add(types.InlineKeyboardButton("🔙 Retour Accueil", callback_data="back_main"))
    return markup

def category_menu(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products.get(category, [])):
        name = p["name"]
        qty = stock.get(category, {}).get(name, 0)
        if qty > 0:
            markup.add(types.InlineKeyboardButton(
                f"{name} — {p['price']}€ (x{qty})", 
                callback_data=f"add_{category}_{i}"
            ))
    markup.add(types.InlineKeyboardButton("🛍 Voir mon panier", callback_data="view_cart"))
    markup.add(types.InlineKeyboardButton("🔙 Retour Produits", callback_data="menu_produits"))
    return markup

# ==================== HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 **Bonjour et bienvenue sur le bot !**", 
                     parse_mode='Markdown', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    user_id = call.from_user.id

    if call.data == "menu_produits":
        bot.edit_message_text("🛒 **Nos Produits**\nChoisissez une enseigne :", 
                              chat_id, msg_id, reply_markup=produits_menu(), parse_mode='Markdown')

    elif call.data == "menu_recharger":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for amt in [10, 20, 50]:
            markup.add(types.InlineKeyboardButton(f"{amt} €", callback_data=f"recharge_{amt}"))
        markup.add(types.InlineKeyboardButton("🔙 Retour", callback_data="back_main"))
        bot.edit_message_text("💰 **Recharger via PayPal**", chat_id, msg_id, reply_markup=markup)

    elif call.data.startswith("recharge_"):
        amount = int(call.data.split("_")[1])
        link = f"https://paypal.me/{PAYPAL_USERNAME}/{amount}EUR"
        bot.send_message(chat_id, f"💰 **Recharge de {amount}€**\n\nPayez ici :\n{link}")

    elif call.data.startswith("cat_"):
        cat = call.data[4:]
        bot.edit_message_text(f"📋 **{cat.replace('_', ' ').title()}**", 
                              chat_id, msg_id, reply_markup=category_menu(cat), parse_mode='Markdown')

    elif call.data.startswith("add_"):
        _, cat, idx = call.data.split("_")
        idx = int(idx)
        p = products[cat][idx]
        name = p["name"]

        if stock.get(cat, {}).get(name, 0) <= 0:
            bot.answer_callback_query(call.id, "❌ Plus en stock !")
            return

        carts[user_id][name] = carts[user_id].get(name, 0) + 1
        stock[cat][name] -= 1
        save_stock(stock)
        bot.answer_callback_query(call.id, f"✅ {name} ajouté !")

    elif call.data == "view_cart":
        bot.send_message(chat_id, "🛍 Panier en cours de développement...")

    elif call.data == "back_main":
        bot.edit_message_text("👋 **Accueil**", chat_id, msg_id, reply_markup=main_menu(), parse_mode='Markdown')

    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['restock'])
def restock(message):
    global stock
    stock = load_stock()
    for cat in stock:
        for name in stock[cat]:
            stock[cat][name] = 15
    save_stock(stock)
    bot.send_message(message.chat.id, "✅ **Stock rechargé à 15 unités par produit !**")

# Lancement
if __name__ == "__main__":
    print("🤖 Bot démarré avec succès sur Railway ! (avec stock)")
    bot.infinity_polling(none_stop=True)
