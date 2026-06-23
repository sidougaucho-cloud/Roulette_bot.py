import telebot
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TOKEN MANQUANT")
    exit(1)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Bot fonctionne ! /start OK")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "Je suis en ligne !")

print("🤖 Bot démarré avec succès - Test simple")
bot.infinity_polling(none_stop=True)
