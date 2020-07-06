# Generated by Django 2.2 on 2020-06-12 13:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scg_app', '0078_auto_20200604_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='marcaje',
            name='from_nettime',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='marcaje',
            name='usuario',
            field=models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
