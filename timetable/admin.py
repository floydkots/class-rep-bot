from django.contrib import admin
from django.db import models
from django import forms
from .models import (Unit, Course, StudentClass, Student, Lecturer, Venue, Period, Lesson)


class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name',)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)


class StudentClassAdmin(admin.ModelAdmin):
    def s_units(self):
        return ', '.join(str(unit) for unit in self.units.all())

    list_display = ('year', 'course', 'semester', s_units,)
    list_display_links = list_display


class StudentAdmin(admin.ModelAdmin):
    def units(self):
        return ', '.join(str(unit) for unit in self.student_class.units.all())

    list_display = ('name', 'mobile', units, 'email', 'username', 'chat_id',)
    list_display_links = ('name', 'mobile', 'email')


class UnitInline(admin.TabularInline):
    model = Unit
    show_change_link = True

    extra = 1


class LecturerForm(forms.ModelForm):
    # fields = ('name', 'mobile', 'email', 'username', 'chat_id')
    class Meta:
        model = Lecturer
        exclude = []

    units = forms.ModelMultipleChoiceField(queryset=Unit.objects.all())

    def __init__(self, *args, **kwargs):
        super(LecturerForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['units'].initial = self.instance.unit_set.all()

    def save(self, *args, **kwargs):
        instance = super(LecturerForm, self).save(commit=False)
        instance.save()
        self.fields['units'].initial.update(lecturer=None)
        self.cleaned_data['units'].update(lecturer=instance)
        return instance


class LecturerAdmin(admin.ModelAdmin):
    form = LecturerForm

    def units(self):
        return ', '.join(str(unit) for unit in self.unit_set.all())

    # inlines = [UnitInline]

    list_display = ('name', units, 'mobile', 'email', 'chat_id', 'username')


class VenueAdmin(admin.ModelAdmin):
    def lessons(self):
        return [item for item in self.lesson_set.all()]

    def number_of_lessons(self):
        return self.lesson_set.all().count()
    list_display = ('name', number_of_lessons, 'longitude', 'latitude', lessons)


class PeriodAdmin(admin.ModelAdmin):
    def lesson(self):
        return [item for item in self.lesson_set.all()]
    list_display = ('day', lesson)
    list_display_links = list_display


class LessonAdmin(admin.ModelAdmin):
    list_display = ('unit', 'period', 'venue', 'type', 'lecturer',)
    list_display_links = ('unit', 'period', 'venue')


admin.site.register(Unit, UnitAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(StudentClass, StudentClassAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Period, PeriodAdmin)
admin.site.register(Lesson, LessonAdmin)


