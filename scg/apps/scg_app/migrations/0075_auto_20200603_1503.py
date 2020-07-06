# Generated by Django 2.2 on 2020-06-03 18:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0074_auto_20200602_1651'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comentario',
            options={'get_latest_by': '-fecha', 'ordering': ['-fecha', '-hora'], 'verbose_name': 'Comentario', 'verbose_name_plural': 'Comentarios'},
        ),
        migrations.AlterModelOptions(
            name='grupocomentario',
            options={'get_latest_by': '-fecha', 'ordering': ['-fecha', '-hora'], 'verbose_name': 'Grupo de comentarios', 'verbose_name_plural': 'Grupos de comentarios'},
        ),
        migrations.RemoveField(
            model_name='clase',
            name='comentario',
        ),
        migrations.AddField(
            model_name='comentario',
            name='hora',
            field=models.TimeField(default=datetime.time(15, 3, 11, 436218)),
        ),
        migrations.AddField(
            model_name='grupocomentario',
            name='hora',
            field=models.TimeField(default=datetime.time(15, 3, 11, 436218)),
        ),
        migrations.AlterField(
            model_name='comentario',
            name='accion',
            field=models.CharField(blank=True, choices=[('gestion_ausencia', 'Gestión Ausencia'), ('gestion_reemplazo', 'Gestión Reemplazo'), ('confirmacion', 'Confirmación'), ('edicion', 'Edición'), ('cancelacion', 'Cancelación'), ('comentario', 'Comentario')], max_length=50, null=True),
        ),
    ]
