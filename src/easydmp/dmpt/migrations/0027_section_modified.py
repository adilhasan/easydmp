# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-06 08:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmpt', '0026_optional_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]