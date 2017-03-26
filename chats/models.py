from django.db import models
"""
I'd like to describe models that hold data on the chats with various students and lecturers
"""
from timetable.models import Student, Lecturer


class StudentChat(models.Model):
    student = models.ForeignKey(to=Student, on_delete=models.CASCADE, null=True)

    chat_id = models.CharField(max_length=15, unique=True)

    mobile_code = models.CharField(max_length=6)
    email_code = models.CharField(max_length=6)
    mobile_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    latest_chat = models.DateTimeField(auto_now=True)


class LecturerChat(models.Model):
    lecturer = models.ForeignKey(to=Lecturer, on_delete=models.CASCADE)

    chat_id = models.CharField(max_length=15, unique=True)

    mobile_code = models.CharField(max_length=6)
    email_code = models.CharField(max_length=6)
    mobile_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    latest_chat = models.DateTimeField(auto_now=True)



