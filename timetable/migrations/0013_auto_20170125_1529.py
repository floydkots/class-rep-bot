# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-25 12:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0012_auto_20170120_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='venue',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='timetable.Venue'),
        ),
    ]
