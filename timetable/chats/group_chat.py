import os
import django
import logging
import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import ParseMode
from timetable.utils import StudentChatting
from timetable.models import Student


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)


def today():
    return datetime.datetime.today().strftime("%A")


def get_inline_markup(frame=None):

    if frame == "Today":
        keyboard = [
            [InlineKeyboardButton("<< Today >>", callback_data="Today"),
             InlineKeyboardButton("This Week", callback_data="This Week")]
        ]

    elif frame == "This Week":
        keyboard = [
            [InlineKeyboardButton("Today", callback_data="Today"),
             InlineKeyboardButton("<< This Week >>", callback_data="This Week")]
        ]

    else:
        keyboard = [
            [InlineKeyboardButton("Today", callback_data="Today"),
             InlineKeyboardButton("This Week", callback_data="This Week")]
        ]

    return InlineKeyboardMarkup(keyboard)


def lessons(bot, update):
    # TODO find a way to determine if it's a lecturer or student, currently assuming a student

    if update.message.chat.type == 'private':
        chat_id = update.message.chat_id
    else:
        chat_id = update.message.from_user.id
    chat = StudentChatting(chat_id=chat_id)
    if chat.student:
        message = chat.get_day_lessons_string(today())
        reply_markup = get_inline_markup(frame="Today")
        update.message.reply_text(message,
                                  reply_markup=reply_markup,
                                  parse_mode=ParseMode.MARKDOWN)
    elif update.message.chat.type == 'group' and update.message.chat_id == -176518514:
        message = "Please register first. Let's chat in private"
        keyboard = [[InlineKeyboardButton(
            text="Chat in Private",
            url="http://t.me/ClassRepBot?start=register")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )


def lessons_particular(bot, update):
    chat_id = update.callback_query.from_user.id
    chat = StudentChatting(chat_id=chat_id)
    query = update.callback_query
    if chat.student:
        if query.data == 'Today':
            bot.editMessageText(text=chat.get_day_lessons_string(today()),
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                reply_markup=get_inline_markup(frame=query.data),
                                parse_mode=ParseMode.MARKDOWN)
        elif query.data == 'This Week':
            bot.editMessageText(text=chat.get_week_lessons_string(),
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                reply_markup=get_inline_markup(frame=query.data),
                                parse_mode=ParseMode.MARKDOWN)
    elif update.message.chat.type == 'group' and update.message.chat_id == -176518514:
        message = "Please register first. Let's chat in private"
        keyboard = [[InlineKeyboardButton(
            text="Chat in Private",
            url="http://t.me/ClassRepBot?start=register")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )


def get_group_chat_handlers():
    return [CommandHandler('lessons', lessons),
            CallbackQueryHandler(lessons_particular)]
