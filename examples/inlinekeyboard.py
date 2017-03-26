import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'class_rep_bot.settings')
django.setup()

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TOKEN = os.environ.get('TOKEN')


def start(bot, update):
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data='1'),
         InlineKeyboardButton("Option 2", callback_data='2')],
        [InlineKeyboardButton("Option 3", callback_data='3')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Please choose:', reply_markup=reply_markup
    )


def button(bot, update):
    query = update.callback_query

    bot.editMessageText(
        text="Selected option: %s" % query.data,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )


def help(bot, update):
    update.message.reply_text(
        "Use /start to test this bot."
    )


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))

# Create the Updater and pass it your bot's token.
updater = Updater(TOKEN)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(button))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()