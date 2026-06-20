import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = telebot.TeleBot(TOKEN)

WELCOME_IMAGE = "https://i.postimg.cc/7ZSb4wnv/BC5238CA-BA84-46EC-9A68-5525C7137EFD.png"

def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("🎰 Jouez !", callback_data="jouer"),
        InlineKeyboardButton("💰 Solde", callback_data="solde"),
        InlineKeyboardButton("📥 Recharger", callback_data="recharger")
    )
    markup.add(
        InlineKeyboardButton("📤 Encaisser", callback_data="encaisser"),
        InlineKeyboardButton("🆘 SAV", callback_data="sav")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_photo(message.chat.id, WELCOME_IMAGE, caption="""🌟 **PATOUCH CASINO** 🌟

Bienvenue !

Choisissez une option :""", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.send_message(call.message.chat.id, f"✅ Clique sur : {call.data}")

print("Bot démarré")
bot.infinity_polling()
