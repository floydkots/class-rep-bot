import os
import django
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

# Example of a bot-user conversation using ConversationHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)
TOKEN = os.environ.get('TOKEN')


CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [['Contact', 'Favourite colour'],
                  ['Number of siblings', 'Something else...'],
                  ['Done']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('%s - %s' % (key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(bot, update):
    update.message.reply_text(
        "Hi! My name is Doctor Botter. I will hold a more complex conversation with you."
        "Why don't you tell me something about yourself?",
        reply_markup=markup)

    return CHOOSING


def regular_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    update.message.reply_text('Your %s? Yes, I would love to hear about that!' % text.lower(),
                              reply_markup=ReplyKeyboardMarkup([[KeyboardButton('Send Contact', request_contact=True)]], one_time_keyboard=True,resize_keyboard=True))

    return TYPING_REPLY


def custom_choice(bot, update):
    update.message.reply_text('Alright, please send me the category first, '
                              'for example "Most impressive skill"')

    return TYPING_CHOICE


def received_information(bot, update, user_data):
    if update.message.contact:
        text = '+' + update.message.contact.phone_number
    else:
        text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text("Neat! Just so you know, this is what you already told me:"
                              "%s"
                              "You can tell me more, or change your opinion on something." % facts_to_str(user_data), reply_markup=markup)

    return CHOOSING


def done(bot, update, user_data):
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("I learned these facts about you:"
                              "%s"
                              "Until next time!" % facts_to_str(user_data))
    user_data.clear()

    return ConversationHandler.END


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [RegexHandler('^(Contact|Favourite colour|Number of siblings)$',
                       regular_choice, pass_user_data=True),
            RegexHandler('^Something else...$', custom_choice),
                       ],

            TYPING_CHOICE: [MessageHandler(Filters.text, regular_choice, pass_user_data=True),
                            ],

            TYPING_REPLY: [MessageHandler((Filters.text | Filters.contact),
                                          received_information,
                                          pass_user_data=True),
                           ],
        },
        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

