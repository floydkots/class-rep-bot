"""
This module contains the definitions of the database models and the associated utility
 functions, of:
    1. :class: `timetable.models.Unit`
    2. :class: `timetable.models.Course`
    3. :class: `timetable.models.Lecturer`
    4. :class: `timetable.models.Venue`
    5. :class: `timetable.models.Period`
    6. :class: `timetable.models.Lesson`
    7. :class: `timetable.models.StudentClass`
    8. :class: `timetable.models.Student`
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Unit(models.Model):
    """
    This object represents a Unit offered within a particular semester, for a particular
    course.

    Attributes:
        code (str): The Unit's code as it appears in the curriculum
        name (str): The Unit's name, more like the title
        lecturer (:class: `timetable.models.Lecturer`):
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    lecturer = models.ForeignKey(to='Lecturer', null=True, blank=True)

    def __str__(self):
        """Uses the unit's name for string representation of the model, like in the admin interface"""
        return self.name


class Course(models.Model):
    """
    This object represents a single course offered in the campus.

    Seeing it has no dependencies on other models, this should ideally be the very first data
    object created in the database.

    I am yet to find a way to enter this information via the bot's interface without reliance on
    the web interface.

    Attributes:
        name (str): The name of the course, like BSc. Mechatronics Engineering
    """
    name = models.CharField(max_length=50)

    def __str__(self):
        """Uses the course's name for string representation of the model like in the admin interface"""
        return self.name


class Lecturer(models.Model):
    """
    This object represents a single lecturer in the campus.

    Attributes:
        name (str): The Lecturer's name
        mobile (Optional [str]): The Lecturer's phone number, a maximum length of 15 digits, like
            +254700123456
        email (Optional [str]): The Lecturer's email. It is a (:class: `model.EmailField`) so that
            django's :func:`~django.core.validators.EmailValidator` is used to validate it's input.
        username (Optional [str]): This field represents the lecturer's telegram username
        chat_id (Optional [str]): This field represents the lecturer's telegram chat id.
            Well, I'm storing it as a string, but Telegram gives it as an int. Can't seem to remember
            the logic behind that decision when I made it. Another reason I should have done these
            docs earlier.

    The optional attributes are, well optional because, at the moment, it is possible to add a lecturer
    via the web interface, before the lecturer actually registers with the bot. In that case, only the
    lecturer's name is accessible.
    """
    name = models.CharField(max_length=50)
    mobile = models.CharField(max_length=15, blank=True, null=True, unique=True)
    email = models.EmailField(max_length=50, blank=True, null=True, unique=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    chat_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        """
        Uses the lecturer's name, of if missing, the lecturer's username for string representation
        of the object
        """
        return self.name or self.username

    def clean(self):
        """
        Caveat: Bulk creating will not call this method.

        Cleaning this way because, having blank=True, null=True and
         unique=True on the model's fields brings a challenge.
         The django admin form by default converts a blank field to an
         empty string (""). This then gets saved in the database. While
         trying to enforce database integrity by ensuring uniqueness,
         two records with the same empty string("") in their
         corresponding fields will be non-unique.

         However, I seek to save multiple lecturers by their names
         only, leaving the other fields truly null. The database does
         not consider two null fields to be non-unique.

         So, my solution is to explicitly check for blank fields
         (empty strings) and set them to none, during the clean method.
        Returns:

        """
        if not self.chat_id:
            self.chat_id = None
        if not self.mobile:
            self.mobile = None
        if not self.email:
            self.email = None


class Venue(models.Model):
    """
    This object represents a venue where a lesson is taught.

    Attributes:
        name (str): The name of the venue as in the timetable, and the venue's literal name
        longitude (Optional [decimal]): Represents the venues geographic longitudinal value
        latitude (Optional [decimal]): Represents the venue's geographic latitudinal value

    The latitude and longitude fields of this class will come in handy upon integration with
    a maps application.
    """
    name = models.CharField(max_length=30, unique=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)

    def __str__(self):
        """Uses the object's name in its string representation"""
        return self.name


class Period(models.Model):
    """
    This object represents a single period in the timetable

    Attributes:
        start (datetime.time): Represents the time when the period starts.
        stop (datetime.time): Represents the time when the period stops.
        day (int): Represents the day of the week in which the period occurs.
            This is stored as an integer, mapped to the corresponding day by the
            DAY list.
    """
    DAY = [
        (1, 'Sunday'),
        (2, 'Monday'),
        (3, 'Tuesday'),
        (4, 'Wednesday'),
        (5, 'Thursday'),
        (6, 'Friday'),
        (7, 'Saturday')
    ]
    start = models.TimeField()
    stop = models.TimeField()
    day = models.IntegerField(choices=DAY)

    def __str__(self):
        """Uses the objects day, start and stop times for the object's string representation"""
        return "%s %s - %s" % (self.get_day_display(),
                               self.start.strftime(format='%I:%M %p'),
                               self.stop.strftime(format='%I:%M %p'))

    def clean(self):
        """
        Checks that:
            1. The period does not stop (end) before it starts :-)
            2. The period does not overlap other already existing periods.

        Returns: None

        Raises:
            ValidationError: If any of the validation checks are failed
        """
        if self.stop <= self.start:
            raise ValidationError(_('Stop time cannot be earlier than or equal to start time.'))
        try:
            # Set the current lesson to the first period in the database
            current_lesson = self.lesson_set.all()[0]

            # Use the current_lesson to get the current period
            current_period = Lesson.objects.get(pk=current_lesson.pk).period

            # Use the current_period in the query to get all the other periods.
            # Periods that are on the same day.
            existing = Period.objects.filter(day=self.day).exclude(
                start=current_period.start,
                stop=current_period.stop,
                day=current_period.day
            )

        except IndexError:
            # If there's not a single lesson, just get all the day's existing period.
            existing = Period.objects.filter(day=self.day)

        for exists in existing:
            # Get the later of the existing start, and entered start times of the two periods.
            later_start = max(exists.start, self.start)

            # Get the earlier of the existing stop, and the entered stop times of the two periods.
            earlier_stop = min(exists.stop, self.stop)

            # If the earlier stop time is later than the later start time, then there's a lesson overlap.
            if earlier_stop > later_start:
                raise ValidationError(_("Lesson overlap! \n%s" % (exists.lesson_set.get(period__start=exists.start))))

    class Meta:
        """Enforces a periods uniqueness by checking all the three class's attributes"""
        unique_together = ["start", "stop", "day"]


class Lesson(models.Model):
    """
    This object represents a  single Lesson in the timetable.

    Attributes:
        unit (:class: `timetable.models.Unit`): The unit to be taught
        venue (:class: `timetable.models.Venue`): Where the unit will be taught
        type (int): 'Theory' or 'Practical'. Set to 'Theory' by default.
        period (:class: `timetable.models.Period`): The period, as in start and stop

    The venue, type and period are nullable. This is a workaround about how django's foreign key
    relations work. If a reference object was deleted, it would delete the Lesson. So, with
    `on_delete=models.SET_NULL`, it simply sets the respective fields to `null`.
    """
    TYPE = (
        (1, 'Theory'),
        (2, 'Practical'),
    )
    unit = models.ForeignKey(to=Unit)
    venue = models.ForeignKey(to=Venue, on_delete=models.SET_NULL, null=True)
    type = models.IntegerField(choices=TYPE, default=1, blank=True, null=True)
    period = models.ForeignKey(to=Period, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """Uses the objects period, unit and venue for it's string representation"""
        return "%s, %s, %s" % (self.period, self.unit, self.venue)

    @property
    def lecturer(self):
        """
        Allows me to access the lecturer as a property of the lesson

        Returns: :class:`timetable.models.Lecturer`
        """
        return self.unit.lecturer

    @lecturer.setter
    def lecturer(self, lec):
        """
        The setter method adds the object's unit as the object's lecturer's unit

        Args:
            lec (object): An object of :class: timetable.models.Lecturer

        Returns: None

        """
        lec.unit_set.add(self.unit)


def lesson_post_delete_callback(sender, **kwargs):
    """
    Some hack whenever a lesson is deleted.

    Deletes both the lesson's period and venue whenever a lesson is deleted. Well,
    depending on a few factors.

    Args:
        sender (object): I guess this should be the sender of the post_delete signal. In this
            case, the sender is :class: `timetable.models.Lesson`.
        **kwargs (dict): A dict of key word arguments. Of particular note is the
            'instance' key word argument. It represents the particular instance
            that is to be deleted.

    Returns: None

    """
    try:
        # Since a period is unique to a lesson, delete the period whenever the lesson is deleted.
        if kwargs['instance'].period:
            kwargs['instance'].period.delete()
        # Since venues are not unique to lessons, if the venue belonged to this particular lesson only,
        # delete it.
        if kwargs['instance'].venue.lesson_set.all().count() < 1:
            kwargs['instance'].venue.delete()
    except Period.DoesNotExist:
        pass
    except Venue.DoesNotExist:
        pass

post_delete.connect(lesson_post_delete_callback, sender=Lesson)


class StudentClass(models.Model):
    """
    This object represents a class within which a student is, and to which a lecturer lectures.

    A kinda contrived class, it ties together the Course to the semester, year, units and lessons.
    Each :class: `timetable.models.Student` has to belong to a :class: `timetable.models.StudentClass`.

    Attributes:
        year (int): The class's year, as represented in the `YEAR` tuple.
        semester (int): The current semester, as represented in the `SEMESTER` tuple.
        course (:class: `timetable.models.Course`): The course to which the class belongs.
        units (:class: `timetable.models.Unit`): Represents the units that the class has
            for the particular semester.
        lessons (:class: `timetable.models.Lesson`): Represents the lessons that the class
            has for the particular semester.
    """
    YEAR = (
        (1, 'First'),
        (2, 'Second'),
        (3, 'Third'),
        (4, 'Fourth'),
        (5, 'Fifth'),
        (6, 'Sixth'),
        (7, 'Seventh'),
    )

    SEMESTER = (
        (1, 'First'),
        (2, 'Second'),
    )

    year = models.IntegerField(choices=YEAR)

    semester = models.IntegerField(choices=SEMESTER)

    course = models.ForeignKey(to=Course)

    units = models.ManyToManyField(to=Unit)

    lessons = models.ManyToManyField(to=Lesson)

    class Meta:
        """This defines how the class is represented in django's admin"""
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        """Uses the objects course and year for its string representation"""
        return "%s %s Year" % (self.course, self.get_year_display())


class Student(models.Model):
    """
    This object represents a student in campus.

    Attributes:
        name (str): The student's name
        mobile (Optional [str]): The student's mobile number
        email (Optional [str]): The student's email address
        student_class (:class: `timetable.models.StudentClass`): The class to which the student
            belongs
        username (Optional [str]): The student's Telegram username
        chat_id (Optional [str]): The student's Telegram chat_id

    I am confused as to why I have some of the fields nullable
    """
    name = models.CharField(max_length=50)
    mobile = models.CharField(max_length=15, null=True, blank=True, unique=True)
    email = models.EmailField(max_length=50, null=True, blank=True, unique=True)

    student_class = models.ForeignKey(to=StudentClass)

    username = models.CharField(max_length=50, blank=True, null=True)
    chat_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        """Sets the object's string representation to either the name of the username"""
        return self.name or self.username

    def clean(self):
        """
        Caveat: Bulk create will not call this method.

        Implementing this method, for the same reasons as in the clean method
        (:func: `~models.Lecture.__clean__`) of :class: `timetable.models.Lecturer`.

        Returns: None

        """
        if not self.mobile:
            self.mobile = None
        if not self.email:
            self.email = None
        if not self.chat_id:
            self.chat_id = None
