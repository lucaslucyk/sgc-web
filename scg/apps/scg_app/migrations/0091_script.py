# Generated by Django 2.2 on 2020-06-22 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0090_auto_20200622_1404'),
    ]

    operations = [
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('content', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
