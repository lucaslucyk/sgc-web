from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
import datetime

from django.db.models import Q
from . import utils
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
        return f'{self.nombre}'

    class Meta:
        verbose_name = "Grupo de Actividad"
        verbose_name_plural = "Grupo de Actividades"
        get_latest_by = "id"

class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    grupo = models.ForeignKey('GrupoActividad', on_delete=models.SET(''), null=True, blank=True)

    def __str__(self):
        return f'{self.nombre} | {self.grupo}'

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        get_latest_by = "id"

class MotivoAusencia(models.Model):

    nombre = models.CharField(max_length=50, unique=True, blank=False, null=False)
    genera_pago = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return f'{self.nombre}'

    class Meta:
        verbose_name='Motivo de Ausencia'
        verbose_name_plural = 'Motivos de Ausencia'
        get_latest_by = 'nombre'

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
        """ informs if a person is busy at a certain time range 
            -including *reemplazos* and ignoring cancelled classes- """

        clases = Clase.objects.filter(
            #employee classes or *reemplazos* only
            Q(empleado=self) | Q(reemplazo=self)    
        ).filter(
            #classes of the date
            fecha=fecha,
            #get the ones that start before the end time
            horario_desde__lt=fin
        ).exclude(
            #excludes classes that end before the start time -including it-
            #or canceled
            Q(horario_hasta__lte=inicio) | Q(estado='5')
        ).exists()

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
        return f'{self.nombre}'

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        get_latest_by = "id"

class Saldo(models.Model):
    actividad = models.ForeignKey('Actividad', on_delete=models.CASCADE)
    sede = models.ForeignKey('Sede', on_delete=models.CASCADE)
    
    desde = models.DateField(default=timezone.now)
    hasta = models.DateField(default=timezone.now)

    saldo_asignado = models.PositiveIntegerField(default=0,
        validators=[MinValueValidator(1)], 
        help_text="Mes para el que desea sumar el saldo"
    )
    

    #delete from
    year = models.CharField(max_length=4, choices=settings.ANOS_CHOICES, 
        blank=False, default=settings.ANOS_CHOICES[0][0], help_text="Año"
    )
    saldo_inicial = models.DecimalField(decimal_places=0, max_digits=5, default=0, help_text="Mes para el que desea sumar el saldo")
    saldo_actual = models.DecimalField(decimal_places=0, max_digits=5, default=0)
    periodo = models.CharField(max_length=14, choices=settings.PERIODOS_CHOICES, blank=False, help_text="Periodos de liquidacion")
    #delete to

    @property
    def saldo_disponible(self):
        clases = Clase.objects.filter(
            actividad = self.actividad,
            sede = self.sede,
            fecha__gte = self.desde,
            fecha__lte = self.hasta,
        ).exclude(
            estado = "5"    #canceladas
        ).count()

        return self.saldo_asignado - clases

    @classmethod
    def check_saldos(cls, _sede, _actividad, _desde, _hasta):
        _saldos = cls.objects.filter(
            sede = _sede,
            actividad = _actividad,
            desde__gte = _desde,
            hasta__lte = _hasta,
        )
        saldo_a_favor = True if _saldos else False

        for _saldo in _saldos:
            saldo_a_favor = False if _saldo.saldo_disponible < 1 else saldo_a_favor

        return saldo_a_favor


    def __str__(self):
        return f'{self.saldo_inicial} para {self.actividad.nombre} en {self.sede.nombre}'

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
    empleado = models.ForeignKey('Empleado', on_delete=models.SET(''), null=True)
    actividad = models.ForeignKey('Actividad', on_delete=models.SET(''), null=True)
    sede = models.ForeignKey('Sede', on_delete=models.SET(''), null=True)

    @classmethod
    def in_use(cls, employee, week_day, date_ini, date_end, hour_ini, hour_end):
        """ informs if the range of days and hours is busy by other *Recurrencia* """
        #print(week_day)
        
        recs = cls.objects.filter(
            empleado=employee,
            dia_semana=week_day,
            fecha_desde__lte=date_ini,
            fecha_hasta__gte=date_end
        ).exclude(
            horario_hasta__lte=hour_ini
        ).filter(
            horario_desde__lt=hour_end
        ).exists()

        # if recs:
        #   print(recs.first().dia_semana, "vs", week_day)
        
        return recs

    def __str__(self):
        return f'Los {self.dia_semana} desde el {self.fecha_desde} hasta el \
            {self.fecha_hasta}, \
            de {self.horario_desde} a {self.horario_hasta}'.replace("\t", "")

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

    empleado = models.ForeignKey('Empleado', on_delete=models.SET(''), related_name='empleado')
    reemplazo = models.ForeignKey('Empleado', blank=True, null=True, on_delete=models.SET(''), related_name='reemplazo')
    ausencia = models.ForeignKey('MotivoAusencia', blank=True, null=True, on_delete=models.SET(''), related_name='ausencia')
    confirmada = models.BooleanField(blank=True, default=False)

    modificada = models.BooleanField(blank=True, default=False)
    estado = models.CharField(max_length=1, choices=settings.ESTADOS_CHOICES, null=True, blank=True, default=settings.ESTADOS_CHOICES[0][-1])
    presencia = models.CharField(max_length=12, choices=settings.PRESENCIA_CHOICES, null=True, blank=True, default=settings.PRESENCIA_CHOICES[0][-1])
    comentario = models.CharField(max_length=1000, blank=True, help_text="Aclaraciones para feriados/no laborables con o sin ausencias")

    @property
    def is_cancelled(self):
        return self.estado == settings.ESTADOS_CHOICES[-1][0]

    @property
    def is_present(self):
        return self.presencia == settings.PRESENCIA_CHOICES[-1][0]

    @property
    def was_made(self):
        blocks = BloqueDePresencia.objects.filter(
            empleado=self.empleado,
            fecha=self.fecha,
            inicio__hora__lte=utils.get_min_offset(
                                        _time=self.horario_desde, 
                                        _mins=settings.MINS_TOLERACIA),
            fin__hora__gte=utils.get_min_offset(
                                        _time=self.horario_hasta,
                                        _mins=settings.MINS_TOLERACIA,
                                        _sub=True),
        )
        #
        return True if blocks else False

    def update_status(self):
        """ update the class status according to all its variables  """

        if self.fecha > datetime.date.today():
            self.estado = settings.ESTADOS_CHOICES[0][0]    #pendiente

        if self.was_made:
            self.estado = settings.ESTADOS_CHOICES[1][0]    #realizada
        else:
            self.estado = settings.ESTADOS_CHOICES[0][0]    #pendiente

        if self.ausencia:
            self.estado = settings.ESTADOS_CHOICES[3][0]    #ausencia

        if self.reemplazo:
            self.estado = settings.ESTADOS_CHOICES[2][0]    #reemplazo

        self.save()
        return self.estado
    
    def __str__(self):
        if self.parent_recurrencia:
            return f'{self.actividad}: el {self.dia_semana} {self.fecha} \
                de {self.horario_desde} a {self.horario_hasta}, \
                dictada por {self.empleado}'.replace("\t", "")

    class Meta:
        verbose_name = "Clase"
        verbose_name_plural = "Clases"
        get_latest_by = "id"
        ordering = ["-id"]

# class Ausencia(models.Model):
#   clase = models.ForeignKey('Clase', on_delete=models.SET(''), related_name='related_clase')
#   motivo = models.CharField(max_length=200)

#   def __str__(self):
#       return f'{self.clase} no dictada. Motivo: {self.motivo}'

#   class Meta:
#       verbose_name = "Ausencia"
#       verbose_name_plural = "Ausencias"
#       get_latest_by = "id"

# class Reemplazo(models.Model):
#   clase = models.ForeignKey('Clase', on_delete=models.SET(''), related_name="clase_relat")
#   empleado_reemplazante = models.ForeignKey('Empleado', on_delete=models.SET(''), related_name='emple_relat')

#   def __str__(self):
#       return f'La -{self.clase}- fue dictada por [{self.empleado_reemplazante}]'

#   class Meta:
#       verbose_name = "Reemplazo"
#       verbose_name_plural = "Reemplazos"
#       get_latest_by = "id"


class Marcaje(models.Model):
    empleado = models.ForeignKey('Empleado', on_delete=models.SET(''))
    fecha = models.DateField(blank=True, default=timezone.now)
    entrada = models.TimeField(null=True, blank=True)
    salida = models.TimeField(null=True, blank=True)

    hora = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.empleado} el {self.fecha} a las {self.hora}'
        
    class Meta:
        verbose_name = "Marcaje"
        verbose_name_plural = "Marcajes"
        get_latest_by = "hora"


class BloqueDePresencia(models.Model):
    empleado = models.ForeignKey('Empleado', blank=True, null=True,
        on_delete=models.CASCADE,
    )

    fecha = models.DateField(blank=True, default=timezone.now)

    inicio = models.ForeignKey('Marcaje', 
        blank=True, null=True, on_delete=models.SET(''),
        related_name='inicio',
    )
    fin = models.ForeignKey('Marcaje', 
        blank=True, null=True, on_delete=models.SET(''),
        related_name='fin',
    )
    
    @classmethod
    def recalcular_bloques(cls, empleado, fecha):
        #cls.objects.filter(empleado=empleado, inicio__fecha=fecha).delete()
        cls.objects.filter(empleado=empleado, fecha=fecha).delete()

        #grouped
        _day_clockings = Marcaje.objects.filter(empleado=empleado, fecha=fecha).order_by('hora')
        if not _day_clockings:
            return True

        if len(_day_clockings) != 1:
            for e, s in utils.grouped(_day_clockings, 2):
                bloque = cls()
                bloque.empleado = empleado 
                bloque.inicio = e
                bloque.fin = s
                bloque.fecha = fecha
                bloque.save()

        if len(_day_clockings) % 2:
            last_bloque = cls()
            last_bloque.empleado = empleado
            last_bloque.fecha = fecha
            last_bloque.inicio = _day_clockings.last()
            last_bloque.save()

        return True


    def __repr__(self):
        return f'Presencia({self.inicio}, {self.fin})'

    def __str__(self):
        return f'Presencia de {self.inicio} a {self.fin}'