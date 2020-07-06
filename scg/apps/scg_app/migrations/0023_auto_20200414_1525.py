# Generated by Django 3.0.3 on 2020-04-14 18:25

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0022_auto_20200413_1111'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saldo',
            name='periodo',
        ),
        migrations.RemoveField(
            model_name='saldo',
            name='saldo_actual',
        ),
        migrations.RemoveField(
            model_name='saldo',
            name='saldo_inicial',
        ),
        migrations.RemoveField(
            model_name='saldo',
            name='year',
        ),
        migrations.AlterField(
            model_name='saldo',
            name='saldo_asignado',
            field=models.PositiveIntegerField(default=0, help_text='Cantidad de clases que desea disponibilizar', validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
