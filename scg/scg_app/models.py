from django.conf import settings
from django.db import models
from django.utils import timezone

#from django.db.models import Q
# Create your models here.

class Rol(models.Model):
	ROLES = (
		('a', 'Tipo 1'),
		('b', 'Tipo 2'),
		('c', 'Tipo 3'),
	)

	tipo_rol = models.CharField(max_length=1, choices=ROLES, blank=False , help_text="Roles placeholder de los users.")
	
	def __str__(self):
		return f'{self.tipo_rol}'

	class Meta:
		verbose_name = "Rol"
		verbose_name_plural = "Roles"
		get_latest_by = "id"

class Escala(models.Model):
	nombre = models.CharField(max_length=30)
	grupo = models.ForeignKey('GrupoActividad', on_delete=models.SET(''), null=True, blank=True)
	monto_hora = models.CharField(max_length=10)

	def __str__(self):
		return f'Escala (Monto/Hora) para {self.nombre}: {self.monto_hora}'

	class Meta:
		verbose_name = "Escala"
		verbose_name_plural = "Escalas"
		get_latest_by = "id"

class GrupoActividad(models.Model):
	nombre = models.CharField(max_length=100)

	def __str__(self):
		return f'Grupo de actividades para {self.nombre}'

	class Meta:
		verbose_name = "Grupo de Actividad"
		verbose_name_plural = "Grupo de Actividades"
		get_latest_by = "id"

class Actividad(models.Model):
	nombre = models.CharField(max_length=100)
	grupo = models.ForeignKey('GrupoActividad', on_delete=models.SET(''), null=True, blank=True)

	def __str__(self):
		return f'{self.nombre}'

	class Meta:
		verbose_name = "Actividad"
		verbose_name_plural = "Actividades"
		get_latest_by = "id"

class Empleado(models.Model):

	### from nettime webservice ###
	apellido = models.CharField(max_length=20)
	nombre = models.CharField(max_length=20)
	dni = models.CharField(max_length=8, unique=True)
	legajo = models.CharField(max_length=10, null=True, blank=True)
	empresa = models.CharField(max_length=10, null=True, blank=True)


	### from local ###
	C_TIPO = (
		('rd', 'Relación de Dependencia'),
		('mt', 'Monotributista'),
	)
	C_LIQ = (
		('j', 'Jornal'),
		('m', 'Mensual'),
	)
	tipo = models.CharField(max_length=2, choices=C_TIPO, blank=False)
	liquidacion = models.CharField(max_length=2, choices=C_LIQ, blank=False)

	escala = models.ManyToManyField('Escala')

	def is_busy(self, fecha, inicio, fin):
		""" informs if a person is busy at a certain time range """
		clases = Clase.objects.filter(
			#classes of the date
			fecha=fecha
		).exclude(
			#excludes classes that end before the start time -including it-
			horario_hasta__lte=inicio
		).filter(
			#get the ones that start before the end time
			horario_desde__lt=fin
		).count()	#count of elements

		return clases

	def __str__(self):
		return f'{self.apellido}, {self.nombre}' if {self.nombre} else f'{self.apellido}'

	class Meta:
		verbose_name = "Empleado"
		verbose_name_plural = "Empleados"
		get_latest_by = "id"

class Sede(models.Model):
	nombre = models.CharField(max_length=40)
	tipo = models.CharField(max_length=30, blank=True)

	def __str__(self):
		return f'{self.nombre}, {self.tipo}' if self.tipo else f'{self.nombre}'

	class Meta:
		verbose_name = "Sede"
		verbose_name_plural = "Sedes"
		get_latest_by = "id"

class Saldo(models.Model):
	actividad = models.ForeignKey('Actividad', on_delete=models.SET(''))
	sede = models.ForeignKey('Sede', on_delete=models.SET(''))
	saldo_inicial = models.DecimalField(decimal_places=0, max_digits=5, default=0)
	saldo_actual = models.DecimalField(decimal_places=0, max_digits=5, default=0)
	periodo = models.CharField(max_length=14, choices=settings.PERIODOS_CHOICES, blank=False, help_text="Periodos de liquidacion")
	year = models.CharField(max_length=4, choices=settings.ANOS_CHOICES, blank=False, default=settings.ANOS_CHOICES[0][0], help_text="Año ")

	def __str__(self):
		return f'{self.actividad} en [{self.sede}]: del saldo inicial {self.saldo_inicial}, se dispone de {self.saldo_actual} clases para el año {self.year} y periodo {self.get_periodo_display()}'

	class Meta:
		verbose_name = "Saldo"
		verbose_name_plural = "Saldos"
		get_latest_by = "id"

class Recurrencia(models.Model):
	dia_semana = models.CharField(max_length=9, choices=settings.DIA_SEMANA_CHOICES, blank=True)
	fecha_desde = models.DateField(default=timezone.now)
	fecha_hasta = models.DateField(blank=True)
	horario_desde = models.TimeField(default=timezone.now)
	horario_hasta = models.TimeField(blank=True)
	empleado = empleado = models.ForeignKey('Empleado', on_delete=models.SET(''), null=True)
	actividad = models.ForeignKey('Actividad', on_delete=models.SET(''), null=True)

	@classmethod
	def is_busy(cls, employee, week_day, date_ini, date_end, hour_ini, hour_end):
		""" informs if the range of days and hours is busy by other *Recurrencia* """

		recs = cls.objects.filter(
			empleado=employee,
			dia_semana=week_day,
			fecha_desde__lte=date_ini,
			fecha_hasta__gte=date_end
		).exclude(
			horario_hasta__lte=hour_ini
		).filter(
			horario_desde__lt=hour_end
		).count()

		return recs

	def __str__(self):
		return f'Recurrencia {self.id}: para {self.empleado}, los {self.dia_semana}, del {self.fecha_desde}, al {self.fecha_hasta} (de {self.horario_desde} a {self.horario_hasta})'

	class Meta:
		verbose_name = "Recurrencia"
		verbose_name_plural = "Recurrencias"
		get_latest_by = "id"

class Clase(models.Model):
	parent_recurrencia = models.ForeignKey('Recurrencia', on_delete=models.CASCADE, null=True)
	parent = models.CharField(max_length=200, blank=True)
	creacion = models.DateTimeField(default=timezone.now)
	dia_semana = models.CharField(max_length=9, choices=settings.DIA_SEMANA_CHOICES, blank=True)
	fecha = models.DateField(blank=True, default=timezone.now)
	horario_desde = models.TimeField(blank=True, default=timezone.now)
	horario_hasta = models.TimeField(blank=True, default=timezone.now)
	actividad = models.ForeignKey('Actividad', on_delete=models.SET(''))
	sede = models.ForeignKey('Sede', on_delete=models.SET(''))
	empleado = models.ForeignKey('Empleado', on_delete=models.SET(''))
	modificada = models.BooleanField(blank=True, default=False)
	estado = models.CharField(max_length=1, choices=settings.ESTADOS_CHOICES, null=True, blank=True, default=settings.ESTADOS_CHOICES[0][-1])
	presencia = models.CharField(max_length=12, choices=settings.PRESENCIA_CHOICES, null=True, blank=True, default=settings.PRESENCIA_CHOICES[0][-1])
	comentario = models.CharField(max_length=1000, blank=True, help_text="Aclaraciones para feriados/no laborables con o sin ausencias")

	def __str__(self):
		return f'Clase de {self.actividad} [{self.id}]: el {self.dia_semana} {self.fecha}, de {self.horario_desde} a {self.horario_hasta}, dictada por {self.empleado}' if self.parent_recurrencia else f'[Recurrencia original eliminada ({self.parent}), id: {self.id}]'

	class Meta:
		verbose_name = "Clase"
		verbose_name_plural = "Clases"
		get_latest_by = "id"
		ordering = ["-id"]

class Ausencia(models.Model):
	clase = models.ForeignKey('Clase', on_delete=models.SET(''))
	motivo = models.CharField(max_length=200)

	def __str__(self):
		return f'{self.clase} no dictada. Motivo: {self.motivo}'

	class Meta:
		verbose_name = "Ausencia"
		verbose_name_plural = "Ausencias"
		get_latest_by = "id"

class Reemplazo(models.Model):
	clase = models.ForeignKey('Clase', on_delete=models.SET(''))
	empleado_reemplazante = models.ForeignKey('Empleado', on_delete=models.SET(''))

	def __str__(self):
		return f'La -{self.clase}- fue dictada por [{self.empleado_reemplazante}]'

	class Meta:
		verbose_name = "Reemplazo"
		verbose_name_plural = "Reemplazos"
		get_latest_by = "id"

class Marcaje(models.Model):
	empleado = models.ForeignKey('Empleado', on_delete=models.SET(''))
	fecha = models.DateField(blank=True, default=timezone.now)
	entrada = models.TimeField(null=True, blank=True)
	salida = models.TimeField(null=True, blank=True)

	def __str__(self):
		return f'El empleado {self.empleado} estuvo presente el {self.fecha}, entre las {self.entrada} y {self.salida}.' if self.salida else f'El empleado {self.empleado} ingreso el {self.fecha} a las {self.entrada}.'

	class Meta:
		verbose_name = "Marcaje"
		verbose_name_plural = "Marcajes"
		get_latest_by = "id"
