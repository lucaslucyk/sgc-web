# Generated by Django 3.0.3 on 2020-04-01 19:23

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Actividad',
                'verbose_name_plural': 'Actividades',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Clase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent', models.CharField(blank=True, max_length=200)),
                ('creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('dia_semana', models.CharField(blank=True, choices=[('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miércoles', 'Miércoles'), ('Jueves', 'Jueves'), ('Viernes', 'Viernes'), ('Sabado', 'Sabado'), ('Domingo', 'Domingo')], max_length=9)),
                ('fecha', models.DateField(blank=True, default=django.utils.timezone.now)),
                ('horario_desde', models.TimeField(blank=True, default=django.utils.timezone.now)),
                ('horario_hasta', models.TimeField(blank=True, default=django.utils.timezone.now)),
                ('modificada', models.BooleanField(blank=True, default=False)),
                ('estado', models.CharField(blank=True, choices=[('0', 'Pendiente'), ('1', 'Realizada Normalmente'), ('2', 'Realizada Con Reemplazo'), ('3', 'No Realizada por Ausencia'), ('4', 'No Realizada por Feriado'), ('5', 'Cancelada')], default='Pendiente', max_length=1, null=True)),
                ('presencia', models.CharField(blank=True, choices=[('No Realizada', 'No Realizada'), ('Realizada', 'Realizada')], default='No Realizada', max_length=12, null=True)),
                ('comentario', models.CharField(blank=True, help_text='Aclaraciones para feriados/no laborables con o sin ausencias', max_length=1000)),
                ('actividad', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Actividad')),
            ],
            options={
                'verbose_name': 'Clase',
                'verbose_name_plural': 'Clases',
                'ordering': ['-id'],
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Empleado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apellido', models.CharField(max_length=20)),
                ('nombre', models.CharField(max_length=20)),
                ('dni', models.CharField(max_length=8, unique=True)),
                ('legajo', models.CharField(blank=True, max_length=10, null=True)),
                ('empresa', models.CharField(blank=True, max_length=10, null=True)),
                ('tipo', models.CharField(choices=[('rd', 'Relación de Dependencia'), ('mt', 'Monotributista')], max_length=2)),
                ('liquidacion', models.CharField(choices=[('j', 'Jornal'), ('m', 'Mensual')], max_length=2)),
            ],
            options={
                'verbose_name': 'Empleado',
                'verbose_name_plural': 'Empleados',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='GrupoActividad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Grupo de Actividad',
                'verbose_name_plural': 'Grupo de Actividades',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_rol', models.CharField(choices=[('a', 'Tipo 1'), ('b', 'Tipo 2'), ('c', 'Tipo 3')], help_text='Roles placeholder de los users.', max_length=1)),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roles',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Sede',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=40)),
                ('tipo', models.CharField(blank=True, max_length=30)),
            ],
            options={
                'verbose_name': 'Sede',
                'verbose_name_plural': 'Sedes',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Saldo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saldo_inicial', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('saldo_actual', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('periodo', models.CharField(choices=[('1', '16/01 al 15/02'), ('2', '16/02 al 15/03'), ('3', '16/03 al 15/04'), ('4', '16/04 al 15/05'), ('5', '16/05 al 15/06'), ('6', '16/06 al 15/07'), ('7', '16/07 al 15/08'), ('8', '16/08 al 15/09'), ('9', '16/09 al 15/10'), ('10', '16/10 al 15/11'), ('11', '16/11 al 15/12'), ('12', '16/12 al 15/01')], help_text='Periodos de liquidacion', max_length=14)),
                ('year', models.CharField(choices=[('2020', '2020'), ('2021', '2021'), ('2022', '2022'), ('2023', '2023'), ('2024', '2024'), ('2025', '2025'), ('2026', '2026'), ('2027', '2027'), ('2028', '2028'), ('2029', '2029'), ('2030', '2030'), ('2031', '2031'), ('2032', '2032'), ('2033', '2033'), ('2034', '2034'), ('2035', '2035'), ('2036', '2036'), ('2037', '2037'), ('2038', '2038'), ('2039', '2039'), ('2040', '2040')], default='2020', help_text='Año ', max_length=4)),
                ('actividad', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Actividad')),
                ('sede', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Sede')),
            ],
            options={
                'verbose_name': 'Saldo',
                'verbose_name_plural': 'Saldos',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Reemplazo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clase', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Clase')),
                ('empleado_reemplazante', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Empleado')),
            ],
            options={
                'verbose_name': 'Reemplazo',
                'verbose_name_plural': 'Reemplazos',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Recurrencia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_semana', models.CharField(blank=True, choices=[('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miércoles', 'Miércoles'), ('Jueves', 'Jueves'), ('Viernes', 'Viernes'), ('Sabado', 'Sabado'), ('Domingo', 'Domingo')], max_length=9)),
                ('fecha_desde', models.DateField(default=django.utils.timezone.now)),
                ('fecha_hasta', models.DateField(blank=True)),
                ('horario_desde', models.TimeField(default=django.utils.timezone.now)),
                ('horario_hasta', models.TimeField(blank=True)),
                ('actividad', models.ForeignKey(null=True, on_delete=models.SET(''), to='scg_app.Actividad')),
                ('empleado', models.ForeignKey(null=True, on_delete=models.SET(''), to='scg_app.Empleado')),
            ],
            options={
                'verbose_name': 'Recurrencia',
                'verbose_name_plural': 'Recurrencias',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Marcaje',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(blank=True, default=django.utils.timezone.now)),
                ('entrada', models.TimeField(blank=True, null=True)),
                ('salida', models.TimeField(blank=True, null=True)),
                ('empleado', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Empleado')),
            ],
            options={
                'verbose_name': 'Marcaje',
                'verbose_name_plural': 'Marcajes',
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Escala',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=30)),
                ('monto_hora', models.CharField(max_length=10)),
                ('grupo', models.ForeignKey(blank=True, null=True, on_delete=models.SET(''), to='scg_app.GrupoActividad')),
            ],
            options={
                'verbose_name': 'Escala',
                'verbose_name_plural': 'Escalas',
                'get_latest_by': 'id',
            },
        ),
        migrations.AddField(
            model_name='empleado',
            name='escala',
            field=models.ManyToManyField(to='scg_app.Escala'),
        ),
        migrations.AddField(
            model_name='clase',
            name='empleado',
            field=models.ForeignKey(on_delete=models.SET(''), to='scg_app.Empleado'),
        ),
        migrations.AddField(
            model_name='clase',
            name='parent_recurrencia',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scg_app.Recurrencia'),
        ),
        migrations.AddField(
            model_name='clase',
            name='sede',
            field=models.ForeignKey(on_delete=models.SET(''), to='scg_app.Sede'),
        ),
        migrations.CreateModel(
            name='Ausencia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.CharField(max_length=200)),
                ('clase', models.ForeignKey(on_delete=models.SET(''), to='scg_app.Clase')),
            ],
            options={
                'verbose_name': 'Ausencia',
                'verbose_name_plural': 'Ausencias',
                'get_latest_by': 'id',
            },
        ),
        migrations.AddField(
            model_name='actividad',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(''), to='scg_app.GrupoActividad'),
        ),
    ]
