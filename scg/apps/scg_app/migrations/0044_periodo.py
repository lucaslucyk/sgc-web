# Generated by Django 2.2 on 2020-05-06 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0043_auto_20200429_1431'),
    ]

    operations = [
        migrations.CreateModel(
            name='Periodo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desde', models.DateField(blank=True)),
                ('hasta', models.DateField(blank=True)),
                ('bloqueado', models.BooleanField(blank=True, default=True)),
            ],
            options={
                'verbose_name': 'Periodo',
                'verbose_name_plural': 'Periodos',
                'get_latest_by': 'desde',
            },
        ),
    ]
