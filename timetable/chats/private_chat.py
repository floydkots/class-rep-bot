import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import logging
from timetable.utils import StudentChatting


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)


# These are used both at function level and at global level
# High level named constants used in determining initial chat direction
INIT, VIEW_EDIT, EDIT, VIEW, UNITS_LESSONS, EDIT_LESSONS, EDIT_UNITS, VIEW_UNITS, VIEW_LESSONS = range(9)

# Named constants used in the add_unit, edit_unit and remove_unit functions, respectively.
ADD_UNIT, EDIT_UNIT, REMOVE_UNIT = range(10, 13)

# Named constants used in the add_lesson, edit_lesson and remove_lesson functions, respectively.
ADD_LESSON, EDIT_LESSON, REMOVE_LESSON = range(13, 16)

#  TODO confirm that user doesn't have to /start every time he converses with the bot.


def timetable(bot, update):
    update.message.reply_text(
        "Would you like to /view or /edit the timetable? To end this conversation, you can /cancel .",
        reply_markup=ReplyKeyboardRemove()
    )
    return VIEW_EDIT


def edit(bot, update):
    update.message.reply_text("That is, to edit /units or /lessons? To end this conversation, send /cancel .")
    return EDIT


def view(bot, update):
    update.message.reply_text("That is, to view /units or /lessons? To end this conversation, send /cancel .")
    return VIEW


def edit_units(bot, update, user_data):
    user_data['unit'] = INIT
    update.message.reply_text("Good. So, will you /add, /edit or /remove a unit? Send /cancel to end.")
    return EDIT_UNITS


def add_unit(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    # Named constants used in the add_unit function
    code, name = range(20, 22)

    if user_data['unit'] == INIT:
        update.message.reply_text("Send me the unit code like `ABC 1234`. Or /cancel to stop this conversation.",
                                  parse_mode=ParseMode.MARKDOWN)
        user_data['add_unit'] = code
        user_data['unit'] = None

    elif user_data['add_unit'] == code:
        if chat.valid_unit_code(update.message.text.upper()):
            user_data['unit_code'] = update.message.text.upper()
            update.message.reply_text("Good. Now send me the `UNIT NAME`. /cancel to stop this conversation.",
                                      parse_mode=ParseMode.MARKDOWN)
            user_data['add_unit'] = name

        else:
            update.message.reply_text("Oops, your submission `%s` doesn't match the format `ABC 1234`."
                                      " Please correct then resend."
                                      " /cancel to stop." % update.message.text,
                                      parse_mode=ParseMode.MARKDOWN)
            return ADD_UNIT

    elif user_data['add_unit'] == name:
        user_data['unit_name'] = update.message.text.title()

        if chat.add_unit(code=user_data['unit_code'],
                         name=user_data['unit_name']):
            msg = "Thank you."
        else:
            msg = "Oops! The unit already exists."

        update.message.reply_text("%s\nWould you like to /add, /edit or /remove another unit?"
                                  " /cancel to end the conversation." % msg,
                                  parse_mode=ParseMode.MARKDOWN)

        user_data.clear()
        user_data['edit_unit'] = INIT
        user_data['unit'] = INIT
        return EDIT_UNITS

    return ADD_UNIT


def edit_unit(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    # Used to keep track of state in this function
    code_name, code_name_selected, unit_code, unit_name = range(30, 34)

    if user_data['unit'] == INIT:

        markup = chat.get_markup(chat.get_units(with_code=False))
        if markup is None:
            update.message.reply_text("You have no units.",
                                      reply_markup=ReplyKeyboardRemove())
            return EDIT_UNITS  # Possibly return DONE

        update.message.reply_text("Please select the unit to edit. /cancel to stop this conversation.",
                                  reply_markup=markup)
        user_data['edit_unit'] = code_name
        user_data['unit'] = None

    elif user_data['edit_unit'] == code_name:
        if chat.verify_unit_name(update.message.text):
            user_data['unit_selected'] = update.message.text
        else:
            update.message.reply_text("The unit `%s` doesn't exist. Please correct and resend." % update.message.text)
            return EDIT_UNIT

        update.message.reply_text("Would you like to edit the unit code or the unit name? /cancel to stop.",
                                  reply_markup=ReplyKeyboardMarkup(
                                      [['Code', 'Name']], one_time_keyboard=True))
        user_data['edit_unit'] = code_name_selected

    elif user_data['edit_unit'] == code_name_selected:
        choice = update.message.text
        if choice == 'Code':
            update.message.reply_text("The current unit code is `%s`, send me the new code."
                                      % (chat.get_unit_code(user_data['unit_selected']) or "____"),
                                      reply_markup=ReplyKeyboardRemove(),
                                      parse_mode=ParseMode.MARKDOWN)
            user_data['edit_unit'] = unit_code
        elif choice == 'Name':
            update.message.reply_text("Send me the new unit name.",
                                      reply_markup=ReplyKeyboardRemove())
            user_data['edit_unit'] = unit_name
        else:
            update.message.reply_text(
                "Inappropriate choice.\n"
                "Please select from the custom keyboard",
                reply_markup=ReplyKeyboardMarkup(
                    [['Code', 'Name']],
                    one_time_keyboard=True
                ))
            return EDIT_UNIT

    elif user_data['edit_unit'] == unit_code:
        if chat.valid_unit_code(update.message.text.upper()):
            user_data['unit_code'] = update.message.text.upper()

            if chat.edit_unit(name=user_data['unit_selected'],
                              new_code=user_data['unit_code']):
                update.message.reply_text("Success! Would you like to /add, /edit or /remove another unit?"
                                          "/cancel to stop.",
                                          reply_keyboard=ReplyKeyboardRemove())
                user_data.clear()
                user_data['edit_unit'] = INIT
                user_data['unit'] = INIT
                return EDIT_UNITS
            else:
                update.message.reply_text("Oops! Experienced an error. Please try again.",
                                          reply_keyboard=ReplyKeyboardRemove())
                return EDIT_UNIT

        else:
            update.message.reply_text("Oops, your submission `%s` doesn't match the format `ABC 1234`."
                                      " Please correct and resend." % update.message.text.upper(),
                                      reply_markup=ReplyKeyboardRemove(),
                                      parse_mode=ParseMode.MARKDOWN)
            return EDIT_UNIT

    elif user_data['edit_unit'] == unit_name:
        user_data['unit_name'] = update.message.text.title()
        if chat.edit_unit(name=user_data['unit_selected'],
                          new_name=user_data['unit_name']):
            update.message.reply_text("Success! Would you like to /add, /edit or /remove another unit?"
                                      "/cancel to stop.",
                                      reply_markup=ReplyKeyboardRemove())
            user_data.clear()
            user_data['unit'] = INIT
            user_data['edit_unit'] = INIT
            return EDIT_UNITS
        else:
            update.message.reply_text("Oops! Experienced an error. Please try again later",
                                      reply_markup=ReplyKeyboardRemove())
            return EDIT_UNIT

    return EDIT_UNIT


def remove_unit(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    # Internal states
    selection = range(40, 41)

    if user_data['unit'] == INIT:
        units = chat.get_units(with_code=False)
        if units is None:
            update.message.reply_text("You are unauthorised to remove units.",
                                      reply_markup=ReplyKeyboardRemove())
            return EDIT_UNITS  # Possibly return DONE

        markup = chat.get_markup(units)
        update.message.reply_text("Please select the unit to remove. /cancel to stop this conversation.",
                                  reply_markup=markup)
        user_data['remove_unit'] = selection
        user_data['unit'] = None

    elif user_data['remove_unit'] == selection:
        if chat.verify_unit_name(update.message.text):
            user_data['unit_selected'] = update.message.text
        else:
            update.message.reply_text("The unit `%s` doesn't exist. Please correct and resend." % update.message.text,
                                      parse_mode=ParseMode.MARKDOWN)
            return REMOVE_UNIT

        if chat.remove_unit(user_data['unit_selected']):
            update.message.reply_text("Success! Would you like to /add, /edit or /remove another unit?"
                                      " /cancel to stop.",
                                      reply_markup=ReplyKeyboardRemove())
            user_data.clear()
            user_data['edit_unit'] = INIT
            user_data['unit'] = INIT
            return EDIT_UNITS

    return REMOVE_UNIT


def edit_lessons(bot, update, user_data):
    user_data['lesson'] = INIT
    update.message.reply_text("Good. So, will you /add, /edit or /remove a lesson? Send /cancel to end.")
    return EDIT_LESSONS


def add_lesson(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    # Named constants used in the add_unit function
    unit, period_start, period_stop, period_day, l_type, venue, done = range(50, 57)

    if user_data['lesson'] == INIT:
        markup = chat.get_markup(chat.get_units(with_code=False))
        if markup is None:
            update.message.reply_text(
                "You have no units.",
                reply_markup=ReplyKeyboardRemove())
            return EDIT_LESSONS

        update.message.reply_text("Which unit?",
                                  reply_markup=markup,
                                  parse_mode=ParseMode.MARKDOWN)
        user_data['add_lesson'] = period_start
        user_data['lesson'] = None

    elif user_data['add_lesson'] == period_start:
        if chat.verify_unit_name(update.message.text):
            user_data['unit_selected'] = update.message.text
        else:
            update.message.reply_text(
                "The unit `%s` doesn't exist. "
                "Select from the custom keyboard or add a new unit first."
                % update.message.text,
            )
            return ADD_LESSON
        update.message.reply_text(
            "Lesson starts at?",
            reply_markup=chat.get_markup(chat.get_time_keyboard()),
            parse_mode=ParseMode.MARKDOWN
        )
        user_data['add_lesson'] = period_stop

    elif user_data['add_lesson'] == period_stop:
        if chat.valid_time(update.message.text):
            user_data['period'] = [update.message.text]
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.get_time_keyboard())
            )
            return ADD_LESSON
        update.message.reply_text(
            "Lesson ends at?",
            reply_markup=chat.get_markup(chat.get_time_keyboard())
        )
        user_data['add_lesson'] = period_day

    elif user_data['add_lesson'] == period_day:
        if chat.valid_time(update.message.text):
            user_data['period'].append(update.message.text)
            update.message.reply_text(
                "On which day?",
                reply_markup=chat.get_markup(chat.get_day_keyboard())
            )
            user_data['add_lesson'] = l_type
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.get_time_keyboard())
            )
            return ADD_LESSON

    elif user_data['add_lesson'] == l_type:
        if chat.valid_day(update.message.text):
            user_data['period'].append(update.message.text)
            result = chat.valid_period(user_data['period'])
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.get_day_keyboard())
            )
            return ADD_LESSON

        if result is True:
            update.message.reply_text(
                "Theory or practical?",
                reply_markup=chat.get_markup(chat.lesson_type)
            )
            user_data['add_lesson'] = venue
        elif isinstance(result, str):
            update.message.reply_text(
                "%s\n"
                "Resend. Lesson starts at?\n" % result,
                reply_markup=chat.get_markup(chat.get_time_keyboard())
            )
            user_data['period'] = None
            user_data['add_lesson'] = period_stop

    elif user_data['add_lesson'] == venue:
        if chat.valid_l_type(update.message.text):
            user_data['l_type'] = update.message.text
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.lesson_type)
            )
            return ADD_LESSON
        update.message.reply_text(
            "Venue? _Type it in_",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN
        )
        user_data['add_lesson'] = done

    elif user_data['add_lesson'] == done:
        # TODO find a way to validate submitted venues
        user_data["venue"] = update.message.text
        # Try to generate a lesson object, in case of failure, notify user

        if chat.add_lesson(
            unit=user_data['unit_selected'],
            venue=user_data['venue'].upper(),
            period=user_data['period'],
            l_type=user_data['l_type']
        ):
            update.message.reply_text(
                "Success!\n"
                "/add, /edit or /remove another lesson? /help",
                reply_markup=ReplyKeyboardRemove()
            )
            user_data.clear()
            user_data['lesson'] = INIT
            return EDIT_LESSONS
        else:
            update.message.reply_text(
                "Oops! Experienced an error. Please try again later.",
                reply_markup=ReplyKeyboardRemove()
            )
    return ADD_LESSON


def edit_lesson(bot, update, user_data):
    # Internal states
    lesson_name, lesson_name_selected, period_start, period_stop, period_day, lesson_venue = range(70, 76)
    chat = StudentChatting(chat_id=update.message.chat_id)
    if user_data['lesson'] == INIT:
        markup = chat.get_markup(chat.get_lessons_keyboard())
        if markup is None:
            update.message.reply_text(
                "You have no lessons!",
                reply_markup=ReplyKeyboardRemove()
            )
            return EDIT_LESSONS
        update.message.reply_text(
            "Select the lesson to edit. /cancel to stop",
            reply_markup=markup
        )
        user_data['edit_lesson'] = lesson_name
        user_data['lesson'] = None

    elif user_data['edit_lesson'] == lesson_name:
        if chat.valid_lesson(update.message.text):
            user_data['lesson_selected'] = update.message.text
            update.message.reply_text(
                "Editing its period or venue?"
                "/cancel to stop.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Period', 'Venue']],
                    one_time_keyboard=True
                )
            )
            user_data['edit_lesson'] = lesson_name_selected
        else:
            update.message.reply_text(
                "The lesson \n`%s`\n doesn't exist."
                "Please select from custom keyboard." % update.message.text,
                reply_markup=chat.get_markup(chat.get_lessons_keyboard()),
                parse_mode=ParseMode.MARKDOWN
            )
            return EDIT_LESSON

    elif user_data['edit_lesson'] == lesson_name_selected:
        choice = update.message.text
        if choice == 'Period':
            update.message.reply_text(
                "The current period is `%s`, let's set the new period.\n"
                "Lesson starts at?"
                % (chat.get_lesson_period(user_data['lesson_selected'])),
                reply_markup=chat.get_markup(chat.get_time_keyboard()),
                parse_mode=ParseMode.MARKDOWN
            )
            user_data['edit_lesson'] = period_start
        elif choice == 'Venue':
            update.message.reply_text(
                "The current venue is `%s`, let's set the new venue."
                % (chat.get_lesson_venue(user_data['lesson_selected'])),
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN
            )
            user_data['edit_lesson'] = lesson_venue
        else:
            update.message.reply_text(
                "Oops! Wrong choice.\n"
                "Please select from the custom keyboard",
                reply_markup=ReplyKeyboardMarkup(
                    [['Period', 'Venue']],
                    one_time_keyboard=True
                )
            )
            return EDIT_LESSON

    elif user_data['edit_lesson'] == lesson_venue:
        user_data['venue'] = update.message.text.upper()

        if chat.edit_lesson(
            lesson=user_data['lesson_selected'],
            venue=user_data['venue'],
            period=None
        ):
            update.message.reply_text(
                "Success!\n"
                "/add, /edit or /remove another lesson? /help",
                reply_markup=ReplyKeyboardRemove()
            )
            user_data.clear()
            user_data['edit_lesson'] = INIT
            user_data['lesson'] = INIT
            return EDIT_LESSONS

        else:
            update.message.reply_text(
                "Oops! Experienced an error. Please try again. /help",
                reply_keyboard=ReplyKeyboardRemove()
            )
            return EDIT_LESSONS

    elif user_data['edit_lesson'] == period_start:
        if chat.valid_time(update.message.text):
            user_data['period'] = [update.message.text]
            update.message.reply_text(
                "Lesson ends at?",
                reply_markup=chat.get_markup(chat.get_time_keyboard())
            )
            user_data['edit_lesson'] = period_stop
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.get_time_keyboard())
            )
            return EDIT_LESSON

    elif user_data['edit_lesson'] == period_stop:
        if chat.valid_time(update.message.text):
            user_data['period'].append(update.message.text)
            update.message.reply_text(
                "On which day?",
                reply_markup=chat.get_markup(chat.get_day_keyboard())
            )
            user_data['edit_lesson'] = period_day
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.get_time_keyboard())
            )
            return EDIT_LESSON

    elif user_data['edit_lesson'] == period_day:
        if chat.valid_day(update.message.text):
            user_data['period'].append(update.message.text)
            result = chat.valid_period(
                user_data['period'],
            )
        else:
            update.message.reply_text(
                "Please select from the custom keyboard.",
                reply_markup=chat.get_markup(chat.get_day_keyboard())
            )
            return EDIT_LESSON

        if result is True:
            if chat.edit_lesson(
                lesson=user_data['lesson_selected'],
                period=user_data['period'],
                venue=None
            ):
                update.message.reply_text(
                    "Success!\n"
                    "/add, /edit or /remove another lesson? /help",
                    reply_markup=ReplyKeyboardRemove()
                )
                user_data.clear()
                user_data['edit_lesson'] = INIT
                user_data['lesson'] = INIT
                return EDIT_LESSONS
            else:
                update.message.reply_text(
                    "Oops! Experienced an error. Please try again. /help",
                    reply_keyboard=ReplyKeyboardRemove()
                )
            return EDIT_LESSONS
        elif isinstance(result, str):
            update.message.reply_text(
                "%s\n"
                "Resend. Lesson starts at?" % result,
                reply_keyboard=chat.get_markup(chat.get_time_keyboard())
            )
            user_data['edit_lesson'] = period_start
            user_data['period'] = None

    return EDIT_LESSON

# TODO check editing periods into overlapping periods


def remove_lesson(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    # Internal states
    selection = range(60, 61)

    if user_data['lesson'] == INIT:
        lessons = chat.get_lessons()
        if lessons is None:
            update.message.reply_text(
                "Oops! No lessons to remove.",
                markup=ReplyKeyboardRemove()
            )
            return EDIT_LESSONS

        markup = chat.get_markup(chat.get_lessons_keyboard())
        update.message.reply_text(
            "Select the lesson to remove. /cancel to stop.",
            reply_markup=markup
        )

        user_data['remove_lesson'] = selection
        user_data['lesson'] = None

    elif user_data['remove_lesson'] == selection:
        if chat.valid_lesson(update.message.text):
            user_data['lesson_selected'] = update.message.text
        else:
            update.message.reply_text(
                "The lesson\n `%s`\n doesn't exist. Please correct."
                % update.message.text,
                parse_mode=ParseMode.MARKDOWN
            )
            return REMOVE_UNIT

        if chat.remove_lesson(user_data['lesson_selected']):
            update.message.reply_text(
                "Success! "
                "\nWould you like to /add, /edit or /remove another unit?"
                "\n/help",
                reply_markup=ReplyKeyboardRemove()
            )
            user_data.clear()
            user_data['edit_unit'] = INIT
            user_data['unit'] = INIT
            return EDIT_LESSONS

    return REMOVE_LESSON


def view_units(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    units = chat.get_units(with_code=True)
    if units is None:
        update.message.reply_text("You have no units.",
                                  reply_markup=ReplyKeyboardRemove())
        return VIEW_EDIT

    formatted_units = list()
    units_string = None  # Initializing just to still PyCharm warnings
    for code, name in units:
        formatted_units.append("`%s - %s`" % (code, name))
        units_string = "\n".join(formatted_units).join(['\n', '\n'])
    update.message.reply_text("*SEMESTER UNITS*\n\n"
                              "%s"
                              "\n\nView /lessons or /cancel to end." % units_string,
                              reply_markup=ReplyKeyboardRemove(),
                              parse_mode=ParseMode.MARKDOWN)
    return VIEW


def view_lessons(bot, update, user_data):
    chat = StudentChatting(chat_id=update.message.chat_id)
    lessons = chat.get_lessons()
    if lessons is None:
        update.message.reply_text("You have no lessons.",
                                  reply_markup=ReplyKeyboardRemove())
        return VIEW_EDIT
    s_lessons = str()
    # TODO format lessons to come under their respective days
    # Tuple indices
    # 0 - Period, 1 - Unit, 2 - Venue, 3 - Type, 4 - Lecturer
    update.message.reply_text("%s"
                              "\n/add, /edit or /remove a lesson? /help." %
                              chat.get_lessons_string(),
                              reply_markup=ReplyKeyboardRemove(),
                              parse_mode=ParseMode.MARKDOWN)
    user_data.clear()
    user_data['lesson'] = INIT
    return EDIT_LESSONS


def cancel(bot, update):
    update.message.reply_text('Bye! Thanks for your time. /help',
                              reply_markup=ReplyKeyboardRemove())
    return VIEW_EDIT


def get_timetable_conversation_handler():

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('timetable', timetable),
                      CommandHandler('help', help)],
        states={
            VIEW_EDIT: [CommandHandler('edit', edit),
                        CommandHandler('view', view),
                        CommandHandler('timetable', timetable)],
            EDIT: [CommandHandler('units', edit_units,
                                  pass_user_data=True),
                   CommandHandler('lessons', edit_lessons,
                                  pass_user_data=True)],
            EDIT_UNITS: [CommandHandler('add', add_unit,
                                        pass_user_data=True),
                         CommandHandler('edit', edit_unit,
                                        pass_user_data=True),
                         CommandHandler('remove', remove_unit,
                                        pass_user_data=True)],
            ADD_UNIT: [MessageHandler(Filters.text, add_unit, pass_user_data=True)],
            EDIT_UNIT: [MessageHandler(Filters.text, edit_unit,
                                       pass_user_data=True)],
            REMOVE_UNIT: [MessageHandler(Filters.text, remove_unit,
                                         pass_user_data=True)],
            EDIT_LESSONS: [CommandHandler('add', add_lesson,
                                          pass_user_data=True),
                           CommandHandler('edit', edit_lesson,
                                          pass_user_data=True),
                           CommandHandler('remove', remove_lesson,
                                          pass_user_data=True)],
            ADD_LESSON: [MessageHandler(Filters.text,
                                        add_lesson,
                                        pass_user_data=True)],
            REMOVE_LESSON: [MessageHandler(Filters.text,
                                           remove_lesson,
                                           pass_user_data=True)],
            EDIT_LESSON: [MessageHandler(Filters.text,
                                         edit_lesson,
                                         pass_user_data=True)],
            VIEW: [CommandHandler('units', view_units,
                                  pass_user_data=True),
                   CommandHandler('lessons', view_lessons,
                                  pass_user_data=True)]
        },
        fallbacks=[CommandHandler('cancel', cancel),
                   CommandHandler('timetable', timetable)]
    )

    return conversation_handler

# TODO add error handler to cater for uncaught errors



