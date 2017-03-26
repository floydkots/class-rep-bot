# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-09 11:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Lecturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('mobile', models.CharField(max_length=15)),
                ('email', models.CharField(max_length=30)),
                ('username', models.CharField(max_length=15)),
                ('chat_id', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(choices=[('Theory', 1), ('Practical', 2)], default=1)),
                ('lecturer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetable.Lecturer')),
            ],
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.TimeField()),
                ('stop', models.TimeField()),
                ('day', models.IntegerField(choices=[('Sunday', 1), ('Monday', 2), ('Tuesday', 3), ('Wednesday', 4), ('Thursday', 5), ('Friday', 6), ('Saturday', 7)])),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('mobile', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=30)),
                ('username', models.CharField(max_length=15)),
                ('chat_id', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='StudentClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(choices=[('First', 1), ('Second', 2), ('Third', 3), ('Fourth', 4), ('Fifth', 5)])),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetable.Course')),
            ],
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=15)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=15)),
            ],
        ),
        migrations.AddField(
            model_name='student',
            name='student_class',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetable.StudentClass'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='period',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetable.Period'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetable.Unit'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='venue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetable.Venue'),
        ),
        migrations.AddField(
            model_name='lecturer',
            name='units',
            field=models.ManyToManyField(to='timetable.Unit'),
        ),
        migrations.AddField(
            model_name='course',
            name='units',
            field=models.ManyToManyField(to='timetable.Unit'),
        ),
    ]
