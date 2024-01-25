import telebot
# Replace 'YOUR_BOT_TOKEN' with the token you got from BotFather
from dotenv import load_dotenv
import os

from utils import controller


# Load environment variables from .env file
load_dotenv()

# Get the bot token from the environment variable
TOKEN = os.getenv('BOT_TOKEN')


# You can set parse_mode by default. HTML or MARKDOWN
bot = telebot.TeleBot(token=TOKEN, parse_mode=None)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, """
Welcome to AI Oraichain (V1)! Here is the list of commands : 
/ai tell me stats of 0x9081b50bad8beefac48cc616694c26b027c559bb on eth
/ai how this pool going on eth, pool address 0xe4b8583ccb95b25737c016ac88e539d0605949e8

You can add this bot to any group or use the commands above in this chat. 

Developers: Want to use our data? Reach out to us.
""")


@bot.message_handler(commands=["ai"])
def ohlc(message):
    bot.reply_to(message, "AI is fetching the data..")
    reply = controller(message.text, [])
    bot.reply_to(message, reply)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


if __name__ == '__main__':
    bot.infinity_polling()
