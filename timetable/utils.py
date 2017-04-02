"""This module contains utility functions that sort of interface between chats and models"""

from timetable.models import Unit, Lesson, Student, Venue, Period, Lecturer
import re
from django.core.exceptions import ValidationError
import datetime as dt
import calendar
from telegram import ReplyKeyboardMarkup
#  TODO doc strings


class StudentChatting(object):
    """
    Object representing a student chatting. Interfaces a chat and database models.

    Attributes:
        student: an instance of the Student class from timetable.models

    Args:
        chat_id: Used to lookup the Student object, representing the
            current user of the bot.

    Raises:
        Exception: If no Student object with the supplied `chat_id` exists
    """
    def __init__(self, chat_id):
        assert chat_id is not None
        try:
            self.student = Student.objects.get(chat_id=chat_id)
        except Student.DoesNotExist:
            self.student = None
            raise Exception("No student with chat_id %s exists" % chat_id)

        self.lesson_type = [["Theory"], ["Practical"]]
        self.lessons = dict()

    def get_lessons(self):
        lessons = []
        for item in self.student.student_class.lessons.all():
            lesson = (str(item.period),
                      str(item.unit),
                      str(item.venue),
                      item.get_type_display(),
                      str(item.lecturer) or "")

            self.lessons.update(
                {"\n".join([lesson[0], lesson[1]]): item.pk}
            )

            lessons.append(lesson)

        return lessons

    def get_day_lessons(self):
        lessons = []
        for item in self.student.student_class.lessons.all():
            pass

    def get_lessons_keyboard(self):
        return ["\n".join([ls[0], ls[1]]) for ls in self.get_lessons()]

    def get_units(self, with_code=False):
        """
        Returns the student's particular units, based on his `StudentClass`

        Args:
            with_code (Optional[bool]): Whether to include unit code
                in the returned list of units. Default is False.

        Returns:
            A list of tuples of units in the form (unit name, unit
            code) if `with_code` is set to True, otherwise returns
            list of unit names

        """
        if with_code:
            return [(item.code, item.name) for item in self.student.student_class.units.all()]
        else:
            return [item.name for item in self.student.student_class.units.all()]

    def add_unit(self, code, name):
        unit, created = Unit.objects.get_or_create(code=code, name=name)
        if created:  # New Unit entry made
            self.student.student_class.units.add(unit)
            return True
        else:  # Unit already exists
            return False

    def edit_unit(self, name, new_code=None, new_name=None):
        assert new_code is not None or new_name is not None
        try:
            unit = self.student.student_class.units.get(name=name)
        except Unit.DoesNotExist:
            return False
        if new_code:
            unit.code = new_code
        if new_name:
            unit.name = new_name
        unit.save()
        return True

    def remove_unit(self, name):
        try:
            self.student.student_class.units.get(name=name).delete()
        except Unit.DoesNotExist:
            return False
        return True

    def verify_unit_name(self, name):
        return self.student.student_class.units.filter(name=name).exists()

    def get_unit_code(self, name):
        try:
            unit = self.student.student_class.units.get(name=name)
        except Unit.DoesNotExist:
            return None
        return unit.code

    @staticmethod
    def valid_unit_code(unit_code):
        regex = r"[a-zA-Z]{3} ?\d{4}"  # matches 'ABC 1234'
        return re.match(regex, unit_code)

    @staticmethod
    def valid_time(time_string):
        hours = [(dt.time(i).strftime('%I:%M %p')) for i in range(7, 20)]
        return time_string in hours

    @staticmethod
    def get_day_keyboard():
        return calendar.day_name[:5]

    @staticmethod
    def valid_day(day):
        return day in StudentChatting.get_day_keyboard()

    def valid_l_type(self, l_type):
        return l_type in [t for lt in self.lesson_type for t in lt]

    @staticmethod
    def get_time_keyboard():
        hours = [(dt.time(i).strftime('%I:%M %p')) for i in range(7, 20)]
        x = []
        [x.append([hours[t], hours[t + 6]]) for t in range(6)]
        x.append([hours[12]])
        return x

    @staticmethod
    def get_markup(buttons):
        """
        Accepts list of strings and encodes into custom keyboard.

        Args:
            buttons (Required[list]): List of strings to be button labels

        Returns: None, if buttons is None, otherwise returns the markup
        for the custom keyboard.

        """
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

    def get_lessons_string(self):
        lessons = self.get_lessons()
        lessons_dict = {}

        for day in calendar.day_name[:5]:
            lessons_dict.update({day: []})

        for lesson in lessons:
            lessons_dict[lesson[0].split(' ')[0]].append(lesson)

        lesson_str = str()

        for day in calendar.day_name[:5]:
            s_lesson = "".join("\n%s\n%s (%s)\n%s\n%s\n" % (l[0].split(' ', 1)[-1], l[1], l[3], l[2], l[4]) for l in
                               lessons_dict[day]).join(['*' + day.upper() + '*', '\n\n'])
            lesson_str += s_lesson
        return lesson_str

    def get_day_lessons_string(self, day):
        if day in calendar.day_name[:5]:
            lessons = self.get_lessons()
            l_dict = {day: []}
            for lesson in lessons:
                if lesson[0].startswith(day):
                    l_dict[day].append(lesson)
            return "".join("\n%s\n%s (%s)\n%s\n%s\n" % (l[0].split(' ', 1)[-1], l[1], l[3], l[2], l[4]) for l in
                               l_dict[day]).join(['*TODAY\'S LESSONS*', '\n\n'])

    def get_week_lessons_string(self, week=None):
        # TODO Add a feature for week-specific edits and queries of the timetable
        return "*THIS WEEK'S LESSONS*\n" + self.get_lessons_string()

    @staticmethod
    def valid_period(period):
        try:
            l_period = Period(
                start=dt.datetime.strptime(period[0], '%I:%M %p').time(),
                stop=dt.datetime.strptime(period[1], '%I:%M %p').time(),
                day=calendar.day_name[:5].index(period[2])+2
            )
            l_period.full_clean()
        except ValidationError as ve:
            return '; '.join(ve.messages)
        return True

    def add_lesson(self, unit, venue, period, l_type):
        """
        Creates a new lesson and associates it with the student's class.

        Args:
            unit (Required[str]): Represents the unit to be taught
             during the lesson. The string is the unit name. This
             should have been verified by the calling function via
             verify_unit_name.

             The lecturer is associated to the lesson through the
              unit.
            venue (Required[str]): Represents the location where
             the lesson will happen. The string is the venue name.
            period (Required[list]): of the form [start[time str],stop[time str], day[int]]
             stop[time str], day[int]). Time frame of the lesson.
            l_type (Required[int]): Type of lesson. 1 - Theory,
            2 - Practical.

        Returns: True if successfully created, otherwise returns False

        """
        # Fetch unit
        l_unit = Unit.objects.get(name=unit)

        # Choose an existing venue, otherwise, create a new one
        l_venue, v_created = Venue.objects.get_or_create(name=venue)

        # Period should be unique
        l_period, p_created = Period.objects.get_or_create(
            start=dt.datetime.strptime(period[0], '%I:%M %p').time(),
            stop=dt.datetime.strptime(period[1], '%I:%M %p').time(),
            day=calendar.day_name[:5].index(period[2])+2
        )

        lesson, l_created = Lesson.objects.get_or_create(
            unit=l_unit,
            venue=l_venue,
            period=l_period,
            type=[t for lt in self.lesson_type for t in lt].index(l_type)
        )

        if l_created:
            self.student.student_class.lessons.add(lesson)
            return True
        else:
            return False

    def remove_lesson(self, lesson):
        # FIXME this may not be the most efficient way to go about retrieving the object to be deleted.
        try:
            if not self.lessons:
                self.get_lessons()
            if not self.lessons:
                return False

            self.student.student_class.lessons.get(
                        pk=self.lessons[lesson]).delete()
        except Lesson.DoesNotExist:
            return False
        return True

    def valid_lesson(self, lesson):
        return lesson in [lesson for lesson in self.get_lessons_keyboard()]

    def get_lesson(self, lesson):
        try:
            if not self.lessons:
                self.get_lessons()
            if not self.lessons:
                return None
            lesson = self.student.student_class.lessons.get(
                pk=self.lessons[lesson])
        except Lesson.DoesNotExist:
            return None
        return lesson

    def get_lesson_period(self, lesson):
        lesson = self.get_lesson(lesson)
        if lesson is None:
            return None
        else:
            return lesson.period

    def get_lesson_venue(self, lesson):
        lesson = self.get_lesson(lesson)
        if lesson is None:
            return None
        else:
            return lesson.venue

    def edit_lesson(self, lesson, period=None, venue=None):
        assert period is not None or venue is not None
        lesson = self.get_lesson(lesson)

        if lesson:
            if period:
                lesson.period.start = dt.datetime.strptime(period[0], '%I:%M %p').time()
                lesson.period.stop = dt.datetime.strptime(period[1], '%I:%M %p').time()
                lesson.period.day = calendar.day_name[:5].index(period[2]) + 2
                lesson.period.save()

            if venue:
                lesson.venue.name = venue.upper()
                lesson.venue.save()

            lesson.save()
            return True
        else:
            return False















