# Generated by Django 3.0.3 on 2020-04-10 23:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0019_auto_20200410_1936'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saldo',
            name='mes',
        ),
        migrations.AddField(
            model_name='saldo',
            name='desde',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='saldo',
            name='hasta',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
