# Generated by Django 2.2 on 2020-05-13 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0055_delete_rol'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bloquedepresencia',
            options={'permissions': [('recalculate_blocks', 'Can recalculate blocks of a specific day')]},
        ),
    ]
