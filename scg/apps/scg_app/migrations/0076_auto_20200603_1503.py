# Generated by Django 2.2 on 2020-06-03 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0075_auto_20200603_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentario',
            name='hora',
            field=models.TimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='grupocomentario',
            name='hora',
            field=models.TimeField(auto_now_add=True),
        ),
    ]
