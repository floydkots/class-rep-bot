import os
import django
from telegram.ext import Updater
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

TOKEN = os.environ.get('TOKEN')
updater = Updater(token=TOKEN)
