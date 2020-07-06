# Generated by Django 2.2 on 2020-05-14 20:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0056_auto_20200513_1346'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bloquedepresencia',
            options={'ordering': ['-inicio'], 'permissions': [('recalculate_blocks', 'Can recalculate blocks of a specific day')], 'verbose_name': 'Bloque de presencia', 'verbose_name_plural': 'Bloques de presencia'},
        ),
        migrations.AlterModelOptions(
            name='certificado',
            options={'ordering': ['motivo'], 'verbose_name': 'Certificado', 'verbose_name_plural': 'Certificados'},
        ),
        migrations.AlterModelOptions(
            name='clase',
            options={'get_latest_by': 'id', 'ordering': ['-fecha'], 'permissions': [('confirm', 'Can confirm classes')], 'verbose_name': 'Clase', 'verbose_name_plural': 'Clases'},
        ),
        migrations.AlterModelOptions(
            name='grupoactividad',
            options={'get_latest_by': 'id', 'verbose_name': 'Grupo de Actividad', 'verbose_name_plural': 'Grupos de Actividad'},
        ),
        migrations.AlterModelOptions(
            name='periodo',
            options={'ordering': ['-desde'], 'verbose_name': 'Periodo', 'verbose_name_plural': 'Periodos'},
        ),
    ]
