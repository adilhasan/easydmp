# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-12 13:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plan', '0007_no_sql_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='published',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='published_plans', to=settings.AUTH_USER_MODEL),
        ),
    ]
