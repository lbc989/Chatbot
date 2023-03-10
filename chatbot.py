import logging
import os

import openai
import redis
import telegram.constants
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

openai.api_key = os.getenv('api_key')

MSG_LIST_LIMIT = 20  # int(os.getenv("MSG_LIST_LIMIT", default = 20))


class ChatGPT:
    def __init__(self):
        self.model = "gpt-3.5-turbo-0301"  # os.getenv("OPENAI_MODEL", default = "text-davinci-003")
        self.temperature = 0.9  # float(os.getenv("OPENAI_TEMPERATURE", default = 0))
        self.top_p = 1  # float(os.getenv("OPENAI_TEMPERATURE", default = 0))
        self.frequency_penalty = 0  # float(os.getenv("OPENAI_FREQUENCY_PENALTY", default = 0))
        self.presence_penalty = 0  # float(os.getenv("OPENAI_PRESENCE_PENALTY", default = 0.6))
        self.max_tokens = 1000  # int(os.getenv("OPENAI_MAX_TOKENS", default = 240))

    def get_response(self, user_message):
        response = openai.ChatCompletion.create(
            model=self.model,
            # prompt=self.prompt.generate_prompt(),
            messages=[
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self.max_tokens
        )

        print("AI回答文本：")
        print(response.choices[0].message.content)

        print("AI全部回复內容：")
        print(response)

        return response.choices[0].message.content


class ChatGPT3TelegramBot:

    def __init__(self):
        self.chatgpt = ChatGPT()

    # Help menu
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "/start - Start the bot\n/help - Help menu\n/send - send to bot owner\n/reply - send msg to id")

    async def sendMsg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = context.args[0]  # /add keyword <-- this should store the keyword
        await context.bot.send_message(chat_id="@DawnCat",
                                       text=f'{update.message.from_user.id} {update.message.from_user.name} said: ' + msg)
        await update.message.reply_text('You have sent ' + msg + ' to the owner.')

    async def replyMsg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        id = context.args[0]
        msg = context.args[1]
        await context.bot.send_message(chat_id=id, text=msg)

    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            redis1 = redis.Redis(host=(os.getenv('HOST')), password=(os.getenv('PASSWORD')),
                                 port=(os.getenv('REDISPORT')))
            logging.info(context.args[0])
            msg = context.args[0]  # /add keyword <-- this should store the keyword
            redis1.incr(msg)
            await update.message.reply_text(
                'You have said ' + msg + ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')
        except (IndexError, ValueError):
            await update.message.reply_text('Usage: /add <keyword>')

    # Start the bot
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_allowed(update):
            logging.info(f'User {update.message.from_user.name} is not allowed to start the bot')
            return

        logging.info('Bot started')
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="I'm a gpt-3.5-turbo-0301 Bot, please talk to me!")

    # React to messages
    async def prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_allowed(update):
            logging.info(f'User {update.message.from_user.name} is not allowed to use the bot')
            return

        logging.info(f'New message received from user {update.message.from_user.name}')
        await context.bot.send_chat_action(chat_id=update.effective_chat.id,
                                           action=telegram.constants.ChatAction.TYPING)
        if update.message.voice:
            file = await context.bot.getFile(update.message.voice.file_id)
            print(file)  # oga 文件
            transcription = openai.Audio.transcribe("whisper-1", file)
            print(transcription)
            return
        ai_reply_response = self.get_chatgpt_response(update.message.text)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=ai_reply_response,  # AI回答的內容
            # text=response["message"], # 原始回答
            parse_mode=telegram.constants.ParseMode.MARKDOWN
        )

    def get_chatgpt_response(self, user_message) -> dict:
        try:
            response = self.chatgpt.get_response(user_message)  # ChatGPT的回答

            print("AI回答內容：")
            print(response)

            return response

        except ValueError as e:
            logging.info(f'Error: {e}')
            return {"message": "I'm having some trouble talking to you, please try again later."}

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug(f'Exception while handling an update: {context.error}')

    def is_allowed(self, update: Update) -> bool:

        allowed_chats = ["@DawnCat", "@iamnotroy", "6140146120", "871724721"]  # Please add your Telegram id between "".

        return str(update.message.from_user.id) in allowed_chats or str(update.message.from_user.name) in allowed_chats  # self.config['allowed_chats']

    def run(self):
        # Please add your TelegramBot token between "" below.
        application = ApplicationBuilder().token(os.getenv('ACCESS_TOKEN')).build()
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler("add", self.add))
        application.add_handler(CommandHandler("send", self.sendMsg))
        application.add_handler(CommandHandler("reply", self.replyMsg))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.prompt))
        application.add_handler(MessageHandler(filters.VOICE & (~filters.COMMAND), self.prompt))

        application.add_error_handler(self.error_handler)

        application.run_webhook(listen="0.0.0.0",
                                port=int(os.getenv('PORT')),
                                webhook_url="https://chatbot11.herokuapp.com/")

        #####################################################################


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    telegram_bot = ChatGPT3TelegramBot()

    telegram_bot.run()


if __name__ == '__main__':
    main()
