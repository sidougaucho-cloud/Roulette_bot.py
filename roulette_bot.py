import telebot
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TOKEN MANQUANT")
    exit(1)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ **Le bot marche enfin !**\n\nBonjour, bienvenue !")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.send_message(message.chat.id, "Je suis en ligne ✅")

print("🤖 Bot démarré avec succès sur Railway")
bot.infinity_polling(none_stop=True, interval=1)
