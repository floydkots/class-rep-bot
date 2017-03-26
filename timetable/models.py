from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_delete
from django.dispatch import receiver

# TODO Add doc strings


class Unit(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    lecturer = models.ForeignKey(to='Lecturer', null=True, blank=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Lecturer(models.Model):
    name = models.CharField(max_length=30)
    mobile = models.CharField(max_length=15, blank=True, null=True, unique=True)
    email = models.CharField(max_length=30, blank=True, null=True, unique=True)
    username = models.CharField(max_length=15, blank=True, null=True)
    chat_id = models.CharField(max_length=15, blank=True, null=True, unique=True)

    def __str__(self):
        return self.name or self.username


class Venue(models.Model):
    name = models.CharField(max_length=30, unique=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return self.name


class Period(models.Model):
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
        return "%s %s - %s" % (self.get_day_display(),
                               self.start.strftime(format='%I:%M %p'),
                               self.stop.strftime(format='%I:%M %p'))

    def clean(self):
        if self.stop <= self.start:
            raise ValidationError(_('Stop time cannot be earlier than or equal to start time.'))
        try:
            current_lesson = self.lesson_set.all()[0]
            current_period = Lesson.objects.get(pk=current_lesson.pk).period
            existing = Period.objects.filter(day=self.day).exclude(
                start=current_period.start,
                stop=current_period.stop,
                day=current_period.day
            )

        except IndexError:
            existing = Period.objects.filter(day=self.day)

        for exists in existing:
            later_start = max(exists.start, self.start)
            earlier_stop = min(exists.stop, self.stop)
            if earlier_stop > later_start:
                raise ValidationError(_("Lesson overlap! \n%s" % (exists.lesson_set.get(period__start=exists.start))))

    class Meta:
        unique_together = ["start", "stop", "day"]


class Lesson(models.Model):
    TYPE = (
        (1, 'Theory'),
        (2, 'Practical'),
    )
    unit = models.ForeignKey(to=Unit)
    venue = models.ForeignKey(to=Venue, on_delete=models.SET_NULL, null=True)
    type = models.IntegerField(choices=TYPE, default=1, blank=True, null=True)
    period = models.ForeignKey(to=Period, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return "%s, %s, %s" % (self.period, self.unit, self.venue)

    @property
    def lecturer(self):
        return self.unit.lecturer

    @lecturer.setter
    def lecturer(self, lec):
            lec.unit_set.add(self.unit)


def lesson_post_delete_callback(sender, **kwargs):
    try:
        if kwargs['instance'].period:
            kwargs['instance'].period.delete()
        if kwargs['instance'].venue.lesson_set.all().count() < 1:
            kwargs['instance'].venue.delete()
    except Period.DoesNotExist:
        pass
    except Venue.DoesNotExist:
        pass
post_delete.connect(lesson_post_delete_callback, sender=Lesson)


class StudentClass(models.Model):
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
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return "%s %s Year" % (self.course, self.get_year_display())


class Student(models.Model):
    name = models.CharField(max_length=30)
    mobile = models.CharField(max_length=15, null=True, blank=True, unique=True)
    email = models.EmailField(max_length=30, null=True, blank=True, unique=True)

    student_class = models.ForeignKey(to=StudentClass)

    username = models.CharField(max_length=15, blank=True, null=True)
    chat_id = models.CharField(max_length=15, blank=True, null=True, unique=True)

    def __str__(self):
        return self.name or self.username
