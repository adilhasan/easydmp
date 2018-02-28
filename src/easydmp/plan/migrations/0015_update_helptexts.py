# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-28 08:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0014_plan_doi'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='abbreviation',
            field=models.CharField(blank=True, help_text='A short abbreviation of the plan title, for internal use. Not shown in the generated file.', max_length=8),
        ),
        migrations.AlterField(
            model_name='plan',
            name='title',
            field=models.CharField(help_text='The title of the final plan document itself, used as the\n        topmost header in the generated file. We recommend something that\n        includes the name of the project the plan is for, e.g., "Preliminary\n        data plan for &lt;project&gt;", "Revised data plan for &lt;project&gt;",\n        etc.', max_length=255),
        ),
    ]
