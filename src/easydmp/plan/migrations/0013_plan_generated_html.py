# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-27 09:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0012_plancomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='generated_html',
            field=models.TextField(blank=True),
        ),
    ]
