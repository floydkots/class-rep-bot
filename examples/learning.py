import os
import django
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, Job
from telegram import InlineQueryResultArticle, InputTextMessageContent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

TOKEN = os.environ.get('TOKEN')

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me.")


def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)


def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.sendMessage(chat_id=update.message.chat_id, text=text_caps)


def inline_caps(bot, update):
    query=update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    bot.answerInlineQuery(update.inline_query.id, results)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def callback_minute(bot, job):
    bot.sendMessage(chat_id='@mechatronics2018',
                    text='One message every minute')
    bot.sendMessage(chat_id='190530986',
                    text='One message every minute')


def callback_30(bot, job):
    bot.sendMessage(chat_id='@mechatronics2018',
                    text='A single message with 30s delay')


def callback_increasing(bot, job):
    bot.sendMessage(chat_id="190530986",
                    text='Sending messages with increasing delay up to 10s, then stops.')
    job.interval += 1.0
    if job.interval > 10.0:
        job.schedule_removal()


def callback_alarm(bot, job):
    bot.sendMessage(chat_id=job.context, text='BEEP')


def callback_timer(bot, update, job_queue):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text='Setting a timer for 1 minute!')

    job_alarm = Job(callback_alarm,
                    60.0,
                    repeat=False,
                    context=update.message.chat_id)
    job_queue.put(job_alarm)


def main():
    updater = Updater(token=TOKEN)

    dispatcher = updater.dispatcher
    j = updater.job_queue
    # job_minute = Job(callback_minute, 60.0)
    # j.put(job_minute, next_t=0.0)
    j.put(Job(callback_30, 30.0, repeat=False))
    j.put(Job(callback_increasing, 1.0))

    timer_handler = CommandHandler('timer', callback_timer, pass_job_queue=True)

    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(Filters.text, echo)
    caps_handler = CommandHandler('caps', caps, pass_args=True)
    inline_caps_handler = InlineQueryHandler(inline_caps)
    unknown_handler = MessageHandler(Filters.command, unknown)

    dispatcher.add_handler(timer_handler)
    dispatcher.add_handler(inline_caps_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(caps_handler)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


