# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-09-27 07:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dmpt', '0017_create_model_templateaccess'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateGroupObjectPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TemplateUserObjectPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='template',
            options={'permissions': (('use_template', 'Can use template'),)},
        ),
        migrations.AddField(
            model_name='templateuserobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dmpt.Template'),
        ),
        migrations.AddField(
            model_name='templateuserobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Permission'),
        ),
        migrations.AddField(
            model_name='templateuserobjectpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='templategroupobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dmpt.Template'),
        ),
        migrations.AddField(
            model_name='templategroupobjectpermission',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group'),
        ),
        migrations.AddField(
            model_name='templategroupobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Permission'),
        ),
        migrations.AlterUniqueTogether(
            name='templateuserobjectpermission',
            unique_together=set([('user', 'permission', 'content_object')]),
        ),
        migrations.AlterUniqueTogether(
            name='templategroupobjectpermission',
            unique_together=set([('group', 'permission', 'content_object')]),
        ),
    ]
