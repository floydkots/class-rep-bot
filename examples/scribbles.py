import datetime as dt
import calendar
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

from timetable.models import Lesson
from timetable.utils import StudentChatting

# import calendar
#
# hours = [(dt.time(i).strftime('%I:%M %p')) for i in range(7, 20)]
# x = []
# [x.append([[hours[t]], [hours[t+5]]]) for t in range(6)]
# x.append([hours[12]])
#
# # Convert time string to object
# t_object = dt.datetime.strptime('07:00 AM', '%I:%M %p').time()
#
# days = calendar.day_name
# [print(day) for day in days[:5]]
lesson_dict = {}
chat = StudentChatting(chat_id=190530986)
for day in calendar.day_name[:5]:
    lesson_dict.update({day: []})

lessons = chat.get_lessons()

for lesson in lessons:
    lesson_dict[lesson[0].split(' ')[0]].append(lesson)

lesson_str = str()

for day in calendar.day_name[:5]:
    s_lesson = "".join("\n%s\n%s (%s)\n%s\n%s\n" % (l[0].split(' ', 1)[-1], l[1], l[3], l[2], l[4]) for l in lesson_dict[day]).join(['*'+day.upper()+'*\n', '\n\n'])
    lesson_str += s_lesson


print(lesson_dict)
print(lesson_str)