from django.test import TestCase
from datetime import datetime
from timetable.utils import StudentChatting
from timetable.models import Student, Unit, Lesson, Course, Lecturer, Venue, Period, StudentClass


class StudentChatTestCase(TestCase):
    units = [
        ('EMT 2445', 'Research Methodology for Engineers'),
        ('EMT 2444', 'Microcontroller Programming and Applications'),
        ('EMT 2443', 'Design of Machines and Machine Elements'),
        ('EMT 2442', 'Introduction to Hydraulics and Pneumatics'),
        ('EMT 2441', 'Professional Ethics and Human Values'),
        ('EMT 2440', 'Manufucturing Technology I'),
        ('EMT 2439', 'Design of Mechatronic Systems II'),
        ('EMT 2438', 'Power Electronics')
    ]

    def setUp(self):

        lecturer = Lecturer.objects.create(
            name='Dr. Somebody Someone',
            mobile='+254700000000',
            email='lec@staff.jkuat.ac.ke',
        )

        units = []
        for item in self.units:
            units.append(Unit(code=item[0], name=item[1]))
        Unit.objects.bulk_create(units)

        Unit.objects.get(code='EMT 2445').lecturer = lecturer

        Course.objects.create(
            name='BSc. Mechatronics Engineering'
        )

        Venue.objects.create(name='ELB 114')

        StudentClass.objects.create(
            year=StudentClass.YEAR[3][0],  # 4 - Fourth Year
            semester=StudentClass.SEMESTER[1][0],  # 2 - Second Semester
            course=Course.objects.get(name='BSc. Mechatronics Engineering'),
        )

        Student.objects.create(
            name="Student Somebody",
            mobile="+254701234567",
            email="stud@students.jkuat.ac.ke",
            student_class=StudentClass.objects.get(
                year=StudentClass.YEAR[3][0],
                semester=StudentClass.SEMESTER[1][0]),
            username="studsome",
            chat_id=123456789
        )

        Period.objects.create(
            start=datetime.strptime('07:00:00', '%H:%M:%S').time(),
            stop=datetime.strptime('10:00:00', '%H:%M:%S').time(),
            day=Period.DAY[1][0]  # Monday
        )

        Lesson.objects.create(
            unit=Unit.objects.get(code='EMT 2445'),
            # lecturer=Lecturer.objects.get(pk=1),
            venue=Venue.objects.get(name='ELB 114'),
            type=1,
            period=Period.objects.get(pk=1)
        )

        # Catering for the many-to-many relationship between
        # StudentClass and Units, and Lessons
        # Adding units
        for item in Unit.objects.all():
            StudentClass.objects.get(
                year=StudentClass.YEAR[3][0],
                semester=StudentClass.SEMESTER[1][0]).units.add(item)

        # Adding lessons
        for item in Lesson.objects.all():
            StudentClass.objects.get(
                year=StudentClass.YEAR[3][0],
                semester=StudentClass.SEMESTER[1][0]).lessons.add(item)

        # Add student_chat attribute to be used by all tests.
        self.student_chat = StudentChatting(chat_id=123456789)

    def test_get_units(self):

        self.assertEqual(self.student_chat.get_units(with_code=True), self.units)

    def test_get_lessons(self):
        lesson = Lesson.objects.get(pk=1)
        lesson_list = [(str(lesson.period), str(lesson.unit), str(lesson.venue), ('Theory', 'Practical')[lesson.type], str(lesson.lecturer)) or ""]

        self.assertEqual(self.student_chat.get_lessons(), lesson_list)

    def test_add_unit(self):
        self.student_chat.add_unit(code='XYZ 123',
                                   name='Testing Add Unit')
        self.assertEqual(self.student_chat.student.student_class.units.filter(code='XYZ 123').exists(), True)

    def test_edit_unit(self):
        self.assertEqual(
            self.student_chat.edit_unit(
                name="Power Electronics",
                new_code="XYZ 567"), True)
        self.assertEqual(self.student_chat.student.student_class.units.filter(code='XYZ 567').exists(), True)

        self.assertEqual(
            self.student_chat.edit_unit(
                name="Professional Ethics and Human Values",
                new_name="Professional Human and Ethics Values"), True)
        self.assertEqual(self.student_chat.student.student_class.units.filter(
            name='Professional Human and Ethics Values').exists(), True)

        self.assertEqual(
            self.student_chat.edit_unit(
                name="Design of Machines and Machine Elements",
                new_code="ABC 1235",
                new_name="DMME"), True)
        self.assertEqual(self.student_chat.student.student_class.units.filter(
            code='ABC 1235',
            name="DMME").exists(), True)

    def test_remove_unit(self):
        self.student_chat.remove_unit(name='Power Electronics')
        self.assertEqual(self.student_chat.student.student_class.units.filter(name='Power Electronics').exists(), False)




