# Generated by Django 2.2 on 2020-06-01 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('help', '0004_help_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='help',
            options={'verbose_name': 'Ayuda', 'verbose_name_plural': 'Ayudas'},
        ),
    ]
