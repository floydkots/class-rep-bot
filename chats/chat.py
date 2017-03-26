from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode)
from telegram.keyboardbutton import KeyboardButton
from telegram.ext import (CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
from chats.utils import GeneralChat
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)


# General States
REGISTER, REGISTRATION = range(0, 2)


def start(bot, update, user_data):
    chat = GeneralChat(chat_id=update.message.chat_id)
    reply = (
        "Hi! I am your virtual class rep. "
        "I'll help you in matters class.\n"
    )
    if chat.new:
        message = (
            "\n\nIn order to help meaningfully, I need to know a few things about you. "
            "Please /register to proceed."
            "\nLooking forward to a happy conversation."
        )
        user_data['init'] = REGISTER
    else:
        message = "\nI look forward to a happy conversation.\n" + "Go to /help to see my list of commands"

    update.message.reply_text(
        reply + message,
        reply_markup=ReplyKeyboardRemove()
    )
    return REGISTRATION


def register(bot, update, user_data):
    # Internal states
    name, mobile, email, user_type, student_class, verification = range(20, 26)

    try:
        chat = GeneralChat(chat_id=update.message.chat_id)
    except AttributeError:
        chat = GeneralChat(chat_id=update.callback_query.message.chat_id)

    if user_data['init'] == REGISTER:
        update.message.reply_text(
            "What's your beautiful name? "
            "Please type it in the order of `First-Name Last-Name`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )
        user_data['init'] = None
        user_data['register'] = name
        user_data['username'] = update.message.chat.username
        user_data['chat_id'] = update.message.chat_id

    elif user_data['register'] == name:
        if update.message.text[0].isalpha():
            user_data['name'] = update.message.text.title()
            update.message.reply_text(
                "Nice! What's your mobile number?\n"
                "You could type it (Format: `+254 7xx xxx xxx`), or tap *Send Contact*\n"
                "This will enable me to integrate with the reminders service, besides verifying your authenticity.",
                reply_markup=chat.get_markup(chat.contact_keyboard),
                parse_mode=ParseMode.MARKDOWN
                )

            user_data['register'] = mobile
        else:
            update.message.reply_text(
                "Oops! Names can't start with non-alphabetical characters.",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN
            )
            return REGISTRATION

    elif user_data['register'] == mobile:
        if not update.message.contact:
            update.message.reply_text(
                "Please use the custom keyboard to send your contact",
                reply_markup=chat.get_markup(chat.contact_keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            user_data['mobile'] = '+'+update.message.contact.phone_number

            user_data['register'] = email
            update.message.reply_text(
                "Good! Now, at which email address would you like me to reach you?",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN
            )

    elif user_data['register'] == email:
        if update.message.entities and update.message.entities[0]['type'] == 'email':
            user_data['email'] = update.message.text
            user_data['register'] = user_type
            update.message.reply_text(
                "Almost there! Student or Lecturer?",
                reply_markup=chat.get_markup(chat.user_type_keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text(
                'Please enter a valid email address.',
                reply_markup=ReplyKeyboardRemove(),
            )
    elif user_data['register'] == user_type:
        choice = update.message.text
        if choice != 'Student' and choice != 'Lecturer':
            update.message.reply_text(
                "Please use the custom keyboard.",
                reply_markup=chat.get_markup(chat.user_type_keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            user_data['type'] = choice
            user_data['register'] = None
            if user_data['type'] == 'Student':
                update.message.reply_text(
                    "Which class are you in?",
                    reply_markup=chat.get_markup(chat.get_student_classes()),
                    parse_mode=ParseMode.MARKDOWN
                )
                user_data['register'] = student_class
                chat.is_student()

            elif user_data['type'] == 'Lecturer':
                update.message.reply_text(
                    "Thank you %s"
                    % user_data['name'].split(' ')[0]
                )
                chat.is_lecturer()

                chat.text_verification_code(
                    user_data['mobile'],
                    chat.lecturer_chat.mobile_code
                )
                chat.mail_verification_code(
                    user_data['email'],
                    chat.lecturer_chat.email_code
                )

                update.message.reply_text(
                    "I have sent you *two (2)* different 6-digit verification codes. One to *%s*, and the other to *%s*"
                    "\nDo check them and send me the codes in any order.\n"
                    "And that will be all."
                    % (user_data['email'], user_data['mobile']),
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )
                user_data['register'] = verification

    elif user_data['register'] == student_class:
        if chat.valid_student_class(update.message.text):
            user_data['student_class'] = update.message.text
            update.message.reply_text(
                "Thank you %s"
                % user_data['name'].split(' ')[0]
            )

            chat.text_verification_code(user_data['mobile'], chat.student_chat.mobile_code)
            chat.mail_verification_code(user_data['email'], chat.student_chat.email_code)

            update.message.reply_text(
                "I have sent you *two (2)* different 6-digit verification codes. One to *%s*, and the other to *%s*"
                "\nDo check them and send me the codes in any order.\n"
                "Once I have verified your contacts we'll be good to go."
                "\n\nThe codes may take up to *5 minutes* to arrive. Please wait before tapping *Resend*"
                % (user_data['email'], user_data['mobile']),
                reply_markup=chat.get_verification_markup(),
                parse_mode=ParseMode.MARKDOWN
            )
            user_data['register'] = verification
            user_data['mobile_verified'] = False
            user_data['email_verified'] = False

    elif user_data['register'] == verification:
        if update.message.text == "Resend":
            if not user_data['mobile_verified'] and user_data['email_verified']:
                chat.text_verification_code(user_data['mobile'], chat.student_chat.mobile_code)
                update.message.reply_text(
                    "Resent *mobile* code.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return REGISTRATION
            elif user_data['mobile_verified'] and not user_data['email_verified']:
                chat.mail_verification_code(user_data['email'], chat.student_chat.email_code)
                update.message.reply_text(
                    "Resent *email* code.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return REGISTRATION
            elif not user_data['mobile_verified'] and not user_data['email_verified']:
                chat.text_verification_code(user_data['mobile'], chat.student_chat.mobile_code)
                chat.mail_verification_code(user_data['email'], chat.student_chat.email_code)
                update.message.reply_text(
                    "Resent *mobile* and *email* codes.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return REGISTRATION
        else:
            user_data['code'] = update.message.text
            mobile_verification = chat.verify_mobile_code(user_data)
            email_verification = chat.verify_email_code(user_data)

            if mobile_verification == chat.already_verified:
                update.message.reply_text(
                    "Your mobile number has already been verified.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return REGISTRATION

            elif mobile_verification == chat.newly_verified:
                update.message.reply_text(
                    "Congratulations! Successfully verified your mobile number.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )
                user_data['mobile_verified'] = True
                return REGISTRATION

            if email_verification == chat.already_verified:
                update.message.reply_text(
                    "Your email has already been verified.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return REGISTRATION

            elif email_verification == chat.newly_verified:
                update.message.reply_text(
                    "Congratulations! Successfully verified your email address.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )
                user_data['email_verified'] = True
                return REGISTRATION

            if email_verification == chat.fully_verified or mobile_verification == chat.fully_verified:
                if chat.student_chat:
                    chat.add_student(user_data)
                elif chat.lecturer_chat:
                    chat.add_lecturer(user_data)

                update.message.reply_text(
                    "Awesome! Welcome Aboard.\n\n"
                    "To see my list of commands, go to /help",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )

            if mobile_verification == chat.failed_verification and email_verification == chat.failed_verification:
                update.message.reply_text(
                    "Oops! You sent a wrong verification code.\n"
                    "Please confirm your codes.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return REGISTRATION

    return REGISTRATION

# TODO Find a way to allow for editing of user details


def cancel(bot, update):
    update.message.reply_text(
        'Bye! Thanks for your time. /help',
        reply_markup=ReplyKeyboardRemove()
    )


def get_chats_conversation_handler():
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],
        states={
            REGISTER: [

            ],
            REGISTRATION: [
                CommandHandler('register', register, pass_user_data=True),
                MessageHandler((Filters.text | Filters.contact), register, pass_user_data=True),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return conversation_handler

