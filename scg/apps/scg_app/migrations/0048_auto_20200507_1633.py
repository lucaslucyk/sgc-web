# Generated by Django 2.2 on 2020-05-07 19:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0047_certificado_abs_url'),
    ]

    operations = [
        migrations.RenameField(
            model_name='certificado',
            old_name='abs_url',
            new_name='file_url',
        ),
    ]
