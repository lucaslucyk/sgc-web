# Generated by Django 3.0.3 on 2020-04-24 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0037_auto_20200424_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='empleado',
            name='liquidacion',
            field=models.CharField(blank=True, choices=[('j', 'Jornal'), ('m', 'Mensual')], max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='empleado',
            name='tipo',
            field=models.CharField(blank=True, choices=[('rd', 'Relación de Dependencia'), ('mt', 'Monotributista')], max_length=9, null=True),
        ),
    ]
