# Generated by Django 3.0.3 on 2020-04-12 00:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0020_auto_20200410_2009'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='marcaje',
            options={'get_latest_by': 'hora', 'verbose_name': 'Marcaje', 'verbose_name_plural': 'Marcajes'},
        ),
    ]