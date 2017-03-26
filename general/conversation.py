import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

import logging
from django.conf import settings
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode)
from telegram.ext import (Updater, CommandHandler)
from timetable.chat import get_timetable_conversation_handler
from chats.chat import get_chats_conversation_handler

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# logger = logging.getLogger(__name__)

TOKEN = settings.CLASSREP_BOT_TOKEN


def general_help(bot, update):
    update.message.reply_text(
        "The following is my list of commands.\n\n"
        "/timetable \n",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN)


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('help', general_help))
    dp.add_handler(get_timetable_conversation_handler())
    dp.add_handler(get_chats_conversation_handler())

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

