from django.contrib import admin
from .models import StudentChat, LecturerChat


class StudentChatAdmin(admin.ModelAdmin):
    list_display = ('student', 'chat_id', 'mobile_code', 'email_code', 'mobile_verified', 'email_verified', 'latest_chat')


admin.site.register(StudentChat, StudentChatAdmin)



