# Generated by Django 3.0.3 on 2020-04-08 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0011_auto_20200406_1359'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurrencia',
            name='sede',
            field=models.ForeignKey(null=True, on_delete=models.SET(''), to='scg_app.Sede'),
        ),
    ]
