# Generated by Django 2.2 on 2020-05-29 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0064_auto_20200527_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='sede',
            name='codigo',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='sede',
            name='nombre',
            field=models.CharField(max_length=100),
        ),
    ]
