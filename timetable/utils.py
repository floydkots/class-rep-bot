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
        student (:class: `timetable.objects.Student`): A student
        lesson_type (list): Theory or Practical
        lessons (dict): The student's lessons

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
        """
        Fetches the student's lessons from the database

        Returns:
            lessons (list): A list of the student's lessons, in their respective
                string representations
        """
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
        #TODO implement this function
        lessons = []
        for item in self.student.student_class.lessons.all():
            pass

    def get_lessons_keyboard(self):
        """
        Builds a list structured as a Telegram keyboard.

        Returns:
            (list): A list of lists of the Student's lesson. This is formatted
                in Telegram's keyboard format.
        """
        return ["\n".join([ls[0], ls[1]]) for ls in self.get_lessons()]

    def get_units(self, with_code=False):
        """
        Returns the student's particular units, based on his `StudentClass`

        Args:
            with_code (Optional[bool]): Whether to include unit code
                in the returned list of units. Default is False.

        Returns:
            (list): A list of tuples of units in the form (unit name, unit
            code) if `with_code` is set to True, otherwise returns
            list of unit names

        """
        if with_code:
            return [(item.code, item.name) for item in self.student.student_class.units.all()]
        else:
            return [item.name for item in self.student.student_class.units.all()]

    def add_unit(self, code, name):
        """
        Adds a unit to the student's :class: `timetable.models.StudentClass`.

        Args:
            code (str): The unit's code
            name (str): The unit's name

        Returns:
            (bool): True, if a new unit is created or False otherwise
        """
        unit, created = Unit.objects.get_or_create(code=code, name=name)
        if created:  # New Unit entry made
            self.student.student_class.units.add(unit)
            return True
        else:  # Unit already exists
            return False

    def edit_unit(self, name, new_code=None, new_name=None):
        """
        Edit the student's chosen unit

        Args:
            name (str): The name of the unit
            new_code (Optional [str]): The unit's new code
            new_name (Optional [str]): The unit's new name

        Returns:
            (bool): True if the unit is successfully edited. False if the unit
                does not exist
        """

        # assert that at least a new_code or new_name is given
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
        """
        Delete the student's chosen unit.
        Args:
            name (str): The name of the chose unit

        Returns:
            (bool) : True if the unit is deleted successfully. False otherwise
        """
        try:
            self.student.student_class.units.get(name=name).delete()
        except Unit.DoesNotExist:
            return False
        return True

    def verify_unit_name(self, name):
        """
        Verify that the given name, is the name of an actual unit.

        Args:
            name (str): The name of the unit to be verified

        Returns:
            (bool): True if the unit exists. False otherwise.
        """
        return self.student.student_class.units.filter(name=name).exists()

    def get_unit_code(self, name):
        """
        Retrieve the name of the unit with the given code

        Args:
            name (str): The name of the unit whose code is to be retrieved.

        Returns:
            timetable.models.Unit.code: The code of the unit with the given name.
                Returns None if the unit does not exist.
        """
        try:
            unit = self.student.student_class.units.get(name=name)
        except Unit.DoesNotExist:
            return None
        return unit.code

    @staticmethod
    def valid_unit_code(unit_code):
        """
        Validate the unit code, in terms of its format.

        Args:
            unit_code (str): The unit code to verify

        Returns:
            object: A match object if there is a match. Returns `None` if there is no match.
        """
        # matches 'ABC 1234'
        regex = r"[a-zA-Z]{3} ?\d{4}"
        return re.match(regex, unit_code)

    @staticmethod
    def valid_time(time_string):
        """
        Validates that the submitted time string is within the required range, that is,
        from 7a.m. to 7p.m.

        Args:
            time_string (str): A string representing the time of the day in a format like `07:00 AM`.

        Returns:
            bool: True if the given time_string is in `hours`, the generated list of allowed times.
             False otherwise.
        """
        hours = [(dt.time(i).strftime('%I:%M %p')) for i in range(7, 20)]
        return time_string in hours

    @staticmethod
    def get_day_keyboard():
        """
        Get a list of the days of the week in a Telegram Keyboard format. From `Monday` to `Friday`.
        Could have done it statically. However, it felt nice generating the list in a programmatic way.

        Returns:
            list: A list of the days of the week, in a Telegram keyboard format.
        """
        return calendar.day_name[:5]

    @staticmethod
    def valid_day(day):
        """
        Validates the given day by checking that the string is in the list returned by
        :func: `~timetable.utils.StudentChatting.get_day_keyboard`.

        Args:
            day (str): The day to validate.

        Returns:
            bool: True if the `day` is in the list. False otherwise.
        """
        return day in StudentChatting.get_day_keyboard()

    def valid_l_type(self, l_type):
        """
        Ensures the lesson type is either `Theory` or `Practical`.

        Args:
            l_type (str): The lesson type to validate

        Returns:
            bool: True if `l_type` is in the list of lesson types. False otherwise.

        """
        # Check if the `l_type` is in the list generated from `self.lesson_type`.
        # Thought it better to verify this way, so as to remain DRY.
        return l_type in [t for lt in self.lesson_type for t in lt]

    @staticmethod
    def get_time_keyboard():
        """
        Get a nicely formatted list structure of the allowed time strings.

        Returns:
            x (list): A list of lists of the time strings
        """
        # Generate the list of time strings.
        hours = [(dt.time(i).strftime('%I:%M %p')) for i in range(7, 20)]
        x = []
        # Append to the list, a list of two time strings, with a 6 hour gap.
        [x.append([hours[t], hours[t + 6]]) for t in range(6)]
        # Finally append the last hour.
        x.append([hours[12]])
        return x

    @staticmethod
    def get_markup(buttons):
        """
        Accepts list of strings and encodes into custom keyboard.

        Args:
            buttons (list): List of strings to be button labels

        Returns:
            markup (ReplyKeyboardMarkup): A ReplyKeyboardMarkup object.

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
        """
        Get a nicely formatted string of the lessons that the student has.

        Returns:
            lesson_str (str): A specially formatted string of lessons
        """
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
        """
        Get a nicely formatted string of the lessons in a particular day.

        Args:
            day (str): The day whose lessons are to be returned

        Returns:
            str: String of the lessons of the day.
        """
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
        """
        Validates the submitted period. Checks that there are no overlaps.

        Args:
            period (list): A list of string representations of the following order:
                [start, stop, day]

        Returns:
            bool: True if the period is valid. A string containing the error message otherwise.
        """
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
            unit (str): Represents the unit to be taught
             during the lesson. The string is the unit name. This
             should have been verified by the calling function via
             verify_unit_name.

            venue (str): Represents the location where
             the lesson will happen. The string is the venue name.
            period (list): of the form [start[time string],stop[time string], day[int]].
             Time frame of the lesson.
            l_type (int): Type of lesson. 1 - Theory, 2 - Practical.

        Notes:
            The lecturer is associated to the lesson through the unit.

        Returns:
             bool: True if the lesson is successfully created, otherwise returns False.
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

        # Lesson created if it did not exist
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
        """
        Delete the given lesson

        Args:
            lesson (str): The string representation of the lesson to be deleted

        Returns:
            bool: True if the lesson is successfully deleted. False otherwise.
        """

        # FIXME this may not be the most efficient way to go about retrieving the object to be deleted.
        try:
            if not self.lessons:
                self.get_lessons()
            if not self.lessons:
                return False
            # self.lessons now has the lesson's string representation as the keys, and the lesson's
            # primary key as the value

            self.student.student_class.lessons.get(
                        pk=self.lessons[lesson]).delete()
        except Lesson.DoesNotExist:
            return False
        return True

    def valid_lesson(self, lesson):
        """
        Validate the given lesson

        Args:
            lesson (str): String representation of the lesson to be validated.

        Returns:
            bool: True if the lesson is valid. Otherwise false.

        Validity is determined by checking if the lesson is in the list of lessons for the
        particular student.
        """
        return lesson in [lesson for lesson in self.get_lessons_keyboard()]

    def get_lesson(self, lesson):
        """
        Retrieve the Lesson object based on its string representation

        Args:
            lesson (str): String representation fo the lesson to be retrieved

        Returns:
            timetable.models.Lesson
        """
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
        """

        Retrieve the period within which the given lesson is taught.

        Args:
            lesson (str): String representation of the lesson whose period is to be retrieved.

        Returns:
            timetable.models.Period
        """
        lesson = self.get_lesson(lesson)
        if lesson is None:
            return None
        else:
            return lesson.period

    def get_lesson_venue(self, lesson):
        """
        Retrieve the venue of the given lesson

        Args:
            lesson (str): String representation of the lesson

        Returns:
            timetable.models.Venue
        """
        lesson = self.get_lesson(lesson)
        if lesson is None:
            return None
        else:
            return lesson.venue

    def edit_lesson(self, lesson, period=None, venue=None):
        """
        Edit the student's given lesson. Edit's it for the whole :class:`timetable.models.StudentClass`

        Args:
            lesson (str): String representation of the lesson to be edited
            period (Optional[str]): String representation of the new period
            venue (Optional[str]): String representation of the new venue

        Returns:
            bool: True in case of successful edit. False otherwise.
        """
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















