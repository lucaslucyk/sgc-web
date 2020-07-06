# Generated by Django 3.0.3 on 2020-04-24 16:57

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scg_app', '0035_empleado_id_nettime'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoContrato',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_netTime', models.PositiveIntegerField(default=0, help_text='Para matchear marcajes e importaciones', unique=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('nombre', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Tipo de contrato',
                'verbose_name_plural': 'Tipos de contrato',
                'get_latest_by': 'id_netTime',
            },
        ),
        migrations.CreateModel(
            name='TipoLiquidacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_netTime', models.PositiveIntegerField(default=0, help_text='Para matchear marcajes e importaciones', unique=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('nombre', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Tipo de liquidación',
                'verbose_name_plural': 'Tipos de liquidación',
                'get_latest_by': 'id_netTime',
            },
        ),
        migrations.AlterField(
            model_name='empleado',
            name='id_netTime',
            field=models.PositiveIntegerField(default=0, help_text='Para matchear marcajes e importaciones', unique=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='empleado',
            name='liquidacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scg_app.TipoLiquidacion'),
        ),
        migrations.AlterField(
            model_name='empleado',
            name='tipo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scg_app.TipoContrato'),
        ),
    ]