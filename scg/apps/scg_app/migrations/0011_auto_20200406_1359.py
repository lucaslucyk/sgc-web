# Generated by Django 3.0.3 on 2020-04-06 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0010_auto_20200406_0010'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reemplazo',
            name='clase',
        ),
        migrations.RemoveField(
            model_name='reemplazo',
            name='empleado_reemplazante',
        ),
        migrations.DeleteModel(
            name='Ausencia',
        ),
        migrations.DeleteModel(
            name='Reemplazo',
        ),
    ]