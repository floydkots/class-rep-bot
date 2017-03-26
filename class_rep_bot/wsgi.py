"""
WSGI config for class_rep_bot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

import dotenv

from django.core.wsgi import get_wsgi_application
dotenv.load_dotenv(dotenv.find_dotenv())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")

application = get_wsgi_application()
