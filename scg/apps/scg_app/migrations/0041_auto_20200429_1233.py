# Generated by Django 2.2 on 2020-04-29 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0040_auto_20200424_1427'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='marcaje',
            name='entrada',
        ),
        migrations.RemoveField(
            model_name='marcaje',
            name='salida',
        ),
    ]
