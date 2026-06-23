import telebot
from telebot import types
from collections import defaultdict
import os
import json
from datetime import datetime, date

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYPAL_USERNAME = os.getenv("PAYPAL_USERNAME")

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN manquant")

bot = telebot.TeleBot(TOKEN)

# ==================== STOCK (persisté dans un fichier) ====================
STOCK_FILE = "stock.json"

def load_stock():
    try:
        with open(STOCK_FILE, "r") as f:
            return json.load(f)
    except:
        # Stock par défaut
        default_stock = {}
        for cat, items in products.items():
            default_stock[cat] = {item["name"]: 10 for item in items}  # 10 par produit par défaut
        save_stock(default_stock)
        return default_stock

def save_stock(stock):
    with open(STOCK_FILE, "w") as f:
        json.dump(stock, f, indent=2)

# Chargement initial
products = { ... }  # garde tes produits ici (identique à avant)
stock = load_stock()

# Panier
carts = defaultdict(dict)

# ==================== MENUS (mis à jour avec stock) ====================
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
    if not any(stock.get(category, {}).values()):
        markup.add(types.InlineKeyboardButton("😔 Plus de stock aujourd'hui", callback_data="no_stock"))
    markup.add(types.InlineKeyboardButton("🛍 Voir mon panier", callback_data="view_cart"))
    markup.add(types.InlineKeyboardButton("🔙 Retour Produits", callback_data="menu_produits"))
    return markup

# ==================== RECHARGE STOCK (Admin) ====================
@bot.message_handler(commands=['restock'])
def restock(message):
    # Tu peux sécuriser avec ton ID Telegram plus tard
    for cat in stock:
        for item in products.get(cat, []):
            stock[cat][item["name"]] = 20  # Recharge à 20 par défaut
    save_stock(stock)
    bot.send_message(message.chat.id, "✅ **Stock rechargé pour tous les produits !** (20 unités chacun)")

# ==================== CALLBACKS (mis à jour) ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    user_id = call.from_user.id

    if call.data == "menu_produits":
        bot.edit_message_text("🛒 **Nos Produits**\nChoisissez votre enseigne :", 
                              chat_id, msg_id, reply_markup=produits_menu(), parse_mode='Markdown')

    elif call.data.startswith("cat_"):
        cat = call.data[4:]
        bot.edit_message_text(f"📋 **{cat.replace('_', ' ').title()}**", 
                              chat_id, msg_id, reply_markup=category_menu(cat), parse_mode='Markdown')

    elif call.data.startswith("add_"):
        _, cat, idx = call.data.split("_")
        idx = int(idx)
        product = products[cat][idx]
        name = product["name"]

        if stock.get(cat, {}).get(name, 0) <= 0:
            bot.answer_callback_query(call.id, "❌ Plus en stock !")
            return

        carts[user_id][name] = carts[user_id].get(name, 0) + 1
        stock[cat][name] -= 1
        save_stock(stock)
        
        bot.answer_callback_query(call.id, f"✅ {name} ajouté (stock restant: {stock[cat][name]})")

    # ... (le reste de tes callbacks : view_cart, recharge, etc. restent presque identiques)

    bot.answer_callback_query(call.id)

# Lancement
if __name__ == "__main__":
    print("🤖 Bot avec système de stock démarré sur Railway !")
    bot.infinity_polling(none_stop=True)
