# Generated by Django 2.2 on 2020-06-16 16:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0080_auto_20200616_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='liquidacion',
            name='tipo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tipo', to='scg_app.TipoContrato'),
        ),
    ]
