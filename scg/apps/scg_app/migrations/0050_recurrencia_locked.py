# Generated by Django 2.2 on 2020-05-08 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0049_certificado_locked'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurrencia',
            name='locked',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]