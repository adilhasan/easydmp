# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-09-21 07:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dmpt', '0016_question_obligatory'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='dmpt.Template')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_accesses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='templateaccess',
            unique_together=set([('user', 'template')]),
        ),
    ]
