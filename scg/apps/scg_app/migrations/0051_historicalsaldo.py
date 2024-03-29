# Generated by Django 2.2 on 2020-05-11 15:24

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scg_app', '0050_recurrencia_locked'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalSaldo',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('desde', models.DateField(default=django.utils.timezone.now)),
                ('hasta', models.DateField(default=django.utils.timezone.now)),
                ('saldo_asignado', models.PositiveIntegerField(default=0, help_text='Cantidad de clases que desea disponibilizar', validators=[django.core.validators.MinValueValidator(1)])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('actividad', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='scg_app.Actividad')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('sede', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='scg_app.Sede')),
            ],
            options={
                'verbose_name': 'historical Saldo',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
