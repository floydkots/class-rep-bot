import time
import sendgrid
import smtplib
from sendgrid.helpers.mail import Mail as Sendgrid_Mail
from sendgrid.helpers.mail import *
from urllib.error import HTTPError
from io import BytesIO
from django.conf import settings
from chats.models import StudentChat, LecturerChat
from timetable.models import StudentClass, Student, Lecturer
from django.utils.crypto import get_random_string
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton)
from general.AfricasTalkingGateway import AfricasTalkingGateway, AfricasTalkingGatewayException

from telegram.ext.dispatcher import run_async


class Text(object):
    username = settings.USERNAME
    apikey = settings.APIKEY
    sender = "KOTS"

    def __init__(self, mobile, code):
        self.mobile = mobile
        self.gateway = AfricasTalkingGateway(self.username, self.apikey)
        self.code = code

    def send(self):
        message = "CLASS REP Verification Code: %s" % self.code

        try:
            results = self.gateway.sendMessage(
                to_=self.mobile,
                message_=message,
                from_=self.sender
            )
            for recipient in results:
                # status is either "Success" or "error message"
                print('number=%s;status=%s;messageId=%s;cost=%s' % (
                    recipient['number'],
                    recipient['status'],
                    recipient['messageId'],
                    recipient['cost']))

        except AfricasTalkingGatewayException as e:
                print('Encountered an error while sending: %s' % str(e))


class Mail(object):
    host = settings.HOST
    username = settings.USERNAME
    password = settings.PASSWORD
    apikey = settings.SENDGRID_API_KEY
    from_address = "classrep@kots.io"

    def __init__(self, to, code):
        self.to = to
        self.code = code

    def send(self):
        message = "CLASS REP Verification Code: %s" % self.code
        sg = sendgrid.SendGridAPIClient(
            apikey=self.apikey
        )

        email = Sendgrid_Mail()
        email.set_from(Email('classrep@kots.io'))
        email.set_subject("EMAIL VERIFICATION")
        email.add_content(Content("text/plain", message))
        personalization = Personalization()
        personalization.add_to(Email(self.to))
        email.add_personalization(personalization)
        tracking_settings = TrackingSettings()
        tracking_settings.set_click_tracking(
            ClickTracking(True, True))
        tracking_settings.set_open_tracking(OpenTracking(True))
        email.set_tracking_settings(tracking_settings)

        data = email.get()

        try:
            response = sg.client.mail.send.post(request_body=data)
            print(response.status_code)
            if response.status_code < 200 or response.status_code >= 300:
                raise RuntimeError
        except HTTPError as HE:
            msg = HE.read()
            print(msg)
            raise HTTPError(HE.url, HE.code, HE.reason, HE.headers, BytesIO(msg))


class GeneralChat(object):
    user_type_keyboard = [['Student', 'Lecturer']]
    contact_keyboard = [KeyboardButton(
            text='Send Contact',
            request_contact=True
        )]
    # Verification status
    already_verified, newly_verified, fully_verified, failed_verification = range(4)

    def __init__(self, chat_id):
        assert chat_id is not None
        self.chat_id = chat_id
        self.student_chat = None
        self.lecturer_chat = None
        try:
            self.student_chat = StudentChat.objects.get(chat_id=chat_id)
            if StudentChat.objects.get(student__chat_id=chat_id):
                self.new = False
        except StudentChat.DoesNotExist:
            try:
                self.lecturer_chat = LecturerChat.objects.get(chat_id=chat_id)
                if LecturerChat.objects.get(lecturer__chat_id=chat_id):
                    self.new = False
            except LecturerChat.DoesNotExist:
                self.new = True

    def is_student(self):
        self.student_chat, created = StudentChat.objects.get_or_create(
            chat_id=self.chat_id,
        )
        if created:
            self.student_chat.mobile_code = self.get_code(6)
            self.student_chat.email_code = self.get_code(6)
            self.student_chat.save()
        return True

    def is_lecturer(self):
        self.lecturer_chat, created = LecturerChat.objects.get_or_create(
            chat_id=self.chat_id
        )
        if created:
            self.lecturer_chat.mobile_code = self.get_code(6),
            self.lecturer_chat.email_code = self.get_code(6)
        return True

    @staticmethod
    def get_code(length):
        if not isinstance(length, int):
            raise TypeError(
                "length should be of type `int`, not type %s"
                % type(length)
            )
        return get_random_string(length, allowed_chars='0123456789')

    @staticmethod
    def get_markup(buttons):
        if buttons is None:
            return None
        else:
            reply_keyboard = []
            if isinstance(buttons[0], list):
                reply_keyboard = buttons
            else:
                [reply_keyboard.append([button]) for button in buttons]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            return markup

    @staticmethod
    def get_verification_markup():
        keyboard = [
            ['Resend']
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def get_student_classes(as_objects=False):
        if as_objects:
            return [s_class for s_class in StudentClass.objects.all()]
        else:
            return [str(s_class) for s_class in StudentClass.objects.all()]

    @staticmethod
    def valid_student_class(student_class):
        return student_class in GeneralChat.get_student_classes()

    def add_student(self, user_data):
        s_class_dict = {}
        for s_class in StudentClass.objects.all():
            s_class_dict.update({str(s_class): s_class})

        student = Student.objects.create(
            name=user_data['name'],
            mobile=user_data['mobile'],
            email=user_data['email'],
            student_class=s_class_dict[user_data['student_class']],
            username=user_data['username'],
            chat_id=user_data['chat_id']
        )
        self.student_chat.student = student
        self.student_chat.save()

        return True

    def add_lecturer(self, user_data):

        lecturer = Lecturer.objects.create(
            name=user_data['name'],
            mobile=user_data['mobile'],
            email=user_data['email'],
            username=user_data['username'],
            chat_id=user_data['chat_id']
        )

        self.lecturer_chat.lecturer = lecturer
        self.lecturer_chat.save()

        return True

    def verify_mobile_code(self, user_data):
        if self.student_chat:
            if self.student_chat.mobile_verified and \
                            self.student_chat.mobile_code == user_data['code']:
                if self.student_chat.email_verified:
                    return GeneralChat.fully_verified
                return GeneralChat.already_verified

            if self.student_chat.mobile_code == user_data['code']:
                self.student_chat.mobile_verified = True
                self.student_chat.save()

                if self.student_chat.mobile_verified and self.student_chat.email_verified:
                    return GeneralChat.fully_verified
                else:
                    return GeneralChat.newly_verified

        elif self.lecturer_chat:
            if self.lecturer_chat.mobile_verified and \
                            self.lecturer_chat.mobile_code == user_data['code']:
                if self.lecturer_chat.email_verified:
                    return GeneralChat.fully_verified
                return GeneralChat.already_verified

            if self.lecturer_chat.mobile_code == user_data['code']:
                self.lecturer_chat.mobile_verified = True
                self.lecturer_chat.save()

                if self.lecturer_chat.mobile_verified and self.lecturer_chat.email_verified:
                    return GeneralChat.fully_verified
                else:
                    return GeneralChat.newly_verified
        return GeneralChat.failed_verification

    def verify_email_code(self, user_data):
        try:
            if self.student_chat.email_verified and \
                            self.student_chat.email_code == user_data['code']:
                if self.student_chat.mobile_verified:
                    return GeneralChat.fully_verified
                return GeneralChat.already_verified

            if self.student_chat.email_code == user_data['code']:
                self.student_chat.email_verified = True
                self.student_chat.save()
                if self.student_chat.email_verified and self.student_chat.mobile_verified:
                    return GeneralChat.fully_verified
                else:
                    return GeneralChat.newly_verified
        except KeyError:
            try:
                if self.lecturer_chat.email_verified and \
                                user_data['lecturer_chat'].email_code == user_data['code']:
                    if self.lecturer_chat.mobile_verified:
                        return GeneralChat.fully_verified
                    return GeneralChat.already_verified

                if self.lecturer_chat.email_code == user_data['code']:
                    self.lecturer_chat.email_code = True
                    self.lecturer_chat.save()
                    if self.lecturer_chat.mobile_verified and self.lecturer_chat.email_verified:
                        return GeneralChat.fully_verified
                    else:
                        return GeneralChat.newly_verified
            except KeyError:
                return GeneralChat.failed_verification
        return GeneralChat.failed_verification

    @staticmethod
    @run_async
    def text_verification_code(mobile, code):
        text = Text(
            mobile=mobile,
            code=code
        )
        for count in range(5):
            try:
                text.send()
                break
            except:
                time.sleep(3)

    @staticmethod
    @run_async
    def mail_verification_code(email, code):
        mail = Mail(
            to=email,
            code=code
        )
        for count in range(5):
            try:
                mail.send()
                print("Sent mail successfully!")
                break
            except Exception as e:
                print(e)




