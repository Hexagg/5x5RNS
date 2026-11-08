import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "9209289779:AAGuXZgDgT8F-VS-2tgkGGHRUuQc3J8T6ZQ"

# ЗАМЕНИ НА СВОЙ NGROK-АДРЕС (без слэша в конце)
NGROK_URL = "https://hexagg.github.io/5x5RNS/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для драфта LoL.\n"
        "Нажми на кнопку ниже, чтобы открыть драфт для своей команды."
    )

async def captain1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{NGROK_URL}/captain.html?team=1"
    keyboard = [[InlineKeyboardButton("Открыть драфт (Команда 1)", web_app=WebAppInfo(url=url))]]
    await update.message.reply_text("Ты капитан Команды 1. Нажми кнопку:", reply_markup=InlineKeyboardMarkup(keyboard))

async def captain2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{NGROK_URL}/captain.html?team=2"
    keyboard = [[InlineKeyboardButton("Открыть драфт (Команда 2)", web_app=WebAppInfo(url=url))]]
    await update.message.reply_text("Ты капитан Команды 2. Нажми кнопку:", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("captain1", captain1))
    application.add_handler(CommandHandler("captain2", captain2))
    print("Бот запущен.")
    application.run_polling()

if __name__ == '__main__':
    main()