# Generated by Django 2.2 on 2020-05-29 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0067_grupoactividad_codigo'),
    ]

    operations = [
        migrations.AddField(
            model_name='grupoactividad',
            name='tipo',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
