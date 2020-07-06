# Generated by Django 3.0.3 on 2020-04-24 17:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0039_auto_20200424_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='sede',
            name='id_netTime',
            field=models.PositiveIntegerField(default=0, help_text='Para matchear marcajes e importaciones', unique=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='sede',
            name='tipo',
            field=models.CharField(blank=True, default='Física', max_length=30),
        ),
    ]
