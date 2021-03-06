# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-13 09:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0010_auto_20170113_0940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecturer',
            name='chat_id',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='lecturer',
            name='email',
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='lecturer',
            name='mobile',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='chat_id',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='email',
            field=models.EmailField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='mobile',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='code',
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.AlterField(
            model_name='venue',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='period',
            unique_together=set([('start', 'stop', 'day')]),
        ),
    ]
