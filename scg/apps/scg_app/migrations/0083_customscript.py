# Generated by Django 2.2 on 2020-06-17 14:41

from django.db import migrations, models
import python_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0082_auto_20200616_1336'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomScript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', python_field.fields.PythonCodeField(blank=True, null=True)),
            ],
        ),
    ]
