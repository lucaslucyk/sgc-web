# Generated by Django 3.0.3 on 2020-04-09 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0016_auto_20200408_2119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clase',
            name='dia_semana',
            field=models.CharField(blank=True, choices=[('1', 'Lunes'), ('2', 'Martes'), ('3', 'Miércoles'), ('4', 'Jueves'), ('5', 'Viernes'), ('6', 'Sábado'), ('0', 'Domingo')], max_length=9),
        ),
        migrations.AlterField(
            model_name='recurrencia',
            name='dia_semana',
            field=models.CharField(blank=True, choices=[('1', 'Lunes'), ('2', 'Martes'), ('3', 'Miércoles'), ('4', 'Jueves'), ('5', 'Viernes'), ('6', 'Sábado'), ('0', 'Domingo')], max_length=9),
        ),
    ]
