# Generated by Django 2.2 on 2020-06-17 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0084_delete_customscript'),
    ]

    operations = [
        migrations.AddField(
            model_name='sede',
            name='empresa',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='sede',
            name='sociedad',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]