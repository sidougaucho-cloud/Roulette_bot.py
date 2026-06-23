import telebot
from telebot import types
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN manquant")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Nos produits", callback_data="menu_produits"),
        types.InlineKeyboardButton("💰 Recharger", callback_data="menu_recharger")
    )
    bot.send_message(message.chat.id, "👋 **Bonjour et bienvenue !**\nQue voulez-vous faire ?", 
                     parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "menu_produits":
        bot.send_message(call.message.chat.id, "🛒 Menu produits bientôt disponible")
    elif call.data == "menu_recharger":
        bot.send_message(call.message.chat.id, "💰 Recharge PayPal bientôt disponible")
    bot.answer_callback_query(call.id)

print("🤖 Bot démarré - Test /start")
bot.infinity_polling(none_stop=True)
