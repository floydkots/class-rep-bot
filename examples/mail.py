import os
import django
import smtplib
from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()


def send_mail():
    body = "\r\n".join((
        "From: classrep@kots.io",
        "To: floydkots@gmail.com",
        "Subject: SPOOFING TEST",
        "",
        "This is a message from the class rep"
    ))
    server = smtplib.SMTP(settings.HOST)
    server.login(
        user=settings.USERNAME,
        password=settings.PASSWORD
    )
    server.sendmail(
        from_addr='classrep@kots.io',
        to_addrs=['floydkots@gmail.com'],
        msg=body
    )
    server.quit()

if __name__ == "__main__":
    send_mail()