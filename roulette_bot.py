import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = telebot.TeleBot(TOKEN)

WELCOME_IMAGE = "https://i.postimg.cc/7ZSb4wnv/BC5238CA-BA84-46EC-9A68-5525C7137EFD.png"

def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)   # Pour un affichage en carré / grille
    markup.add(
        InlineKeyboardButton("🎰 Jouez !", callback_data="bet_menu"),
        InlineKeyboardButton("💰 Solde", callback_data="balance"),
        InlineKeyboardButton("📥 Recharger", callback_data="deposit")
    )
    markup.add(
        InlineKeyboardButton("📤 Encaisser", callback_data="withdraw"),
        InlineKeyboardButton("🆘 SAV", callback_data="help")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_photo(
        message.chat.id, 
        WELCOME_IMAGE, 
        caption="""🌟 **PATOUCH CASINO** 🌟

Bienvenue dans le casino le plus prestigieux !

Choisissez une option ci-dessous :""", 
        reply_markup=main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "bet_menu":
        bot.send_message(chat_id, "🪙 Menu des mises en cours de développement...")
    elif call.data == "balance":
        bot.send_message(chat_id, "💰 Solde en cours de développement...")
    elif call.data == "deposit":
        bot.send_message(chat_id, "📥 Recharge en cours de développement...")
    elif call.data == "withdraw":
        bot.send_message(chat_id, "📤 Encaissement en cours de développement...")
    elif call.data == "help":
        bot.send_message(chat_id, "🆘 SAV : Contactez l'admin pour toute aide.")

print("🚀 PATOUCH Casino - Menu principal chargé")
bot.infinity_polling()
