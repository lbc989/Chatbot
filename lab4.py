from telegram import Update
from telegram.ext import ApplicationBuilder, Updater, CommandHandler, MessageHandler, filters, CallbackContext, \
    ContextTypes
import configparser
import logging
import redis
global redis1
def main():

# Load your token and create an Updater for your Bot
    config = configparser.ConfigParser()
    config.read('config.ini')


    application = ApplicationBuilder().token("6248080117:AAH5nAixPYjbRl8zpCNE6R3dnEp9Yb1DeMc").build()
    global redis1
    redis1 = redis.Redis(host=(config['REDIS']['HOST']), password=(config['REDIS']['PASSWORD']), port=(config['REDIS']['REDISPORT']))
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)

    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("hello", hello))
    application.run_polling()


def echo(update, context):

    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Helping you helping you.')


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    user_input = update.message.text
    if user_input.startswith("/hello "):
        await update.message.reply_text("Good day, " + user_input[7:] + "!")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        global redis1
        logging.info(context.args[0])
        msg = context.args[0] # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        await update.message.reply_text(
            'You have said ' + msg + ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /add <keyword>')

if __name__ == '__main__':
    main()