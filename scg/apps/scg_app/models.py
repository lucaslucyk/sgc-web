# -*- coding: utf-8 -*-

### built-in ###
import os
import datetime

### third ###
from multiselectfield import MultiSelectField

### django ###
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator #, MaxValueValidator
from django.shortcuts import reverse
from django.db.models import Q
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation

### own ###
from apps.scg_app import utils

# ### models ###
class Lugar(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, blank=True, null=True, unique=True)
    tipo = models.CharField(
        max_length=50, choices=settings.LUGARES_CHOICES, blank=True, null=True,
        default=settings.LUGARES_CHOICES[0])

    class Meta:
        verbose_name = "Lugar"
        verbose_name_plural = "Lugares"
        ordering = ["nombre", "tipo"]
        get_latest_by = 'nombre'

    def __str__(self):
        return self.nombre
    
    def __repr__(self):
        return "{}(nombre='{}', codigo='{}', tipo='{}')".format(
            self.__class__.__name__,
            self.nombre,
            self.codigo,
            self.tipo,
        )
    
    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model": self.__class__.__name__, "pk": self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('index')

    @property
    def pronombre(self):
        return "el"

class Comentario(models.Model):
    usuario = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    contenido = models.TextField(blank=True)
    fecha = models.DateField(auto_now_add=True, null=True)
    hora = models.TimeField(auto_now_add=True)
    locked = models.BooleanField(null=True, blank=True, default=False)

    accion = models.CharField(
        max_length=50, choices=settings.ACCIONES_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ["-fecha", "-hora"]
        get_latest_by = '-fecha'

    def __str__(self):
        return '{}{}'.format(
            self.contenido[:min(30, len(self.contenido))],
            '...' if len(self.contenido) > 30 else ''
        )

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model": self.__class__.__name__, "pk": self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('clases_view')
    
    @property
    def pronombre(self):
        return "el"

class GrupoComentario(models.Model):
    #fecha = models.DateField(auto_now_add=True, null=True)
    #hora = models.TimeField(auto_now_add=True)

    comentario = models.ForeignKey(
        Comentario, null=True, on_delete=models.CASCADE)

    content_type = models.ForeignKey(
        ContentType, null=True, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    class Meta:
        verbose_name = "Grupo de comentarios"
        verbose_name_plural = "Grupos de comentarios"
        ordering = ["-comentario__fecha", "-comentario__hora"]
        get_latest_by = '-comentario__fecha'

class Periodo(models.Model):
    """ To manage available and blocked periods """

    desde = models.DateField(blank=True)
    hasta = models.DateField(blank=True)
    bloqueado = models.BooleanField(blank=True, default=True)

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ["-desde"]
        get_latest_by = "-desde"

    @classmethod
    def check_overlap(cls, _desde, _hasta, id_exclude=None, locked_only=False):
        """ informs if a period generates an overlap with one already
            created """

        start_before = Q()
        start_before.add(Q(desde__lte=_desde), Q.AND)
        start_before.add(Q(hasta__gte=_desde), Q.AND)

        start_after = Q()
        start_after.add(Q(desde__gte=_desde), Q.AND)
        start_after.add(Q(desde__lte=_hasta), Q.AND)

        period = Q()
        period.add(start_before, Q.OR)
        period.add(start_after, Q.OR)

        _periodos = cls.objects.filter(period)

        if id_exclude:
            _periodos = _periodos.exclude(pk=id_exclude)

        if locked_only:
            _periodos = _periodos.exclude(bloqueado=False)

        return _periodos.count()

    @classmethod
    def blocked_day(cls, day):
        """ inform if a day is blocked by an exist period """

        return cls.check_overlap(day, day, locked_only=True)

    def update_related(self):
        """ update 'locked' property of all corresponding items.
            Return the count affected classes.
        """

        ### clases ###
        clases = Clase.objects.filter(
            fecha__gte=self.desde,
            fecha__lte=self.hasta,
            #locked=not self.bloqueado
        )
        clases.update(locked=self.bloqueado)

        ### certificados ###
        Certificado.objects.filter(
            clases__in=clases
        ).update(locked=self.bloqueado)

        ### recurrencias ###
        r_ids = set(clases.values_list('recurrencia__id', flat=True))
        Recurrencia.objects.filter(pk__in=r_ids).update(locked=self.bloqueado)

        ### marcajes ###
        Marcaje.objects.filter(
            fecha__gte=self.desde,
            fecha__lte=self.hasta,
            locked=not self.bloqueado
        ).exclude(
            from_nettime=True
        ).update(locked=self.bloqueado)

        ### comentarios ###
        Comentario.objects.filter(
            fecha__gte=self.desde,
            fecha__lte=self.hasta,
            locked=not self.bloqueado
        ).update(locked=self.bloqueado)

        return clases.count()

    @classmethod
    def get_date_period(cls, _date):
        """ return period from a specific date, None if no exists """

        period = cls.objects.filter(desde__lte=_date, hasta__gte=_date)
        return period.first() if period else period

    @classmethod
    def get_url_date_period(cls, _date):
        """ return period edit url from a specific date, '#' if no exists """
        
        period = cls.get_date_period(_date)
        return period.get_edit_url() if period else '#'

    @property
    def liquida_mono_url(self):
        liq = self.liquidacion_set.filter(tipo__nombre='Monotributista')
        return liq.first().file.url if liq else ''

    @property
    def liquida_rd_url(self):
        liq = self.liquidacion_set.filter(
            tipo__nombre='Relación de Dependencia')
        return liq.first().file.url if liq else ''

    def get_liquid_mono_url(self):
        """ construct liquid mono url from current object """
        return reverse('liquida_mono', kwargs={"pk": self.id})
    
    def get_liquid_rd_url(self):
        """ construct liquid rd url from current object """
        return reverse('liquida_rd', kwargs={"pk": self.id})

    def get_edit_url(self):
        """ construct edit url from current object """
        return reverse('periodo_update', kwargs={"pk": self.id})

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model": self.__class__.__name__, "pk": self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('periodos_view')

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return f'Desde {self.desde} - Hasta {self.hasta}'

class Escala(models.Model):
    nombre = models.CharField(max_length=30)
    grupo = models.ForeignKey(
        'GrupoActividad', on_delete=models.SET_NULL, null=True, blank=True)
    monto_hora = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"
        ordering = ["nombre",]
        get_latest_by = "nombre"

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return f'{self.monto_hora} AR$/h para {self.grupo.nombre}'

class GrupoActividad(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, blank=True, null=True, unique=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Grupo de Actividad"
        verbose_name_plural = "Grupos de Actividad"
        ordering = ["nombre", ]
        get_latest_by = "nombre"

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return f'{self.nombre}'

class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    grupo = models.ForeignKey(
        'GrupoActividad', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ["nombre", ]
        get_latest_by = "nombre"

    @property
    def pronombre(self):
        return "la"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return f'{self.nombre} | {self.grupo}'

class MotivoAusencia(models.Model):
    id_netTime = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        unique=True,
    )
    nombre = models.CharField(
        max_length=50, unique=True, blank=False, null=False)
    genera_pago = models.BooleanField(blank=True, default=False)
    requiere_certificado = models.BooleanField(blank=True, default=True)

    class Meta:
        verbose_name = 'Motivo de Ausencia'
        verbose_name_plural = 'Motivos de Ausencia'
        ordering = ["nombre", ]
        get_latest_by = 'nombre'

    @classmethod
    def update_from_nettime(cls):
        try:
            incidencias_nt = utils.pull_netTime(
                "TimeType",  # Container
                _fields=["id", "name", "recuperable"],
                _filter='this.timeTypeType != 0'
            )

            for registro in incidencias_nt.get("TimeType"):
                try:
                    motivo = cls.objects.get(id_netTime=registro.get("id"))
                except:
                    motivo = cls.objects.create(id_netTime=registro.get("id"))

                #update employee data
                motivo.nombre = registro.get("name")
                motivo.genera_pago = registro.get("recuperable")
                motivo.save()

        except Exception as error:
            raise error

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return f'{self.nombre}'

class TipoLiquidacion(models.Model):
    id_netTime = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        unique=True,
        help_text="Para matchear marcajes e importaciones")
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Tipo de liquidación"
        verbose_name_plural = "Tipos de liquidación"
        ordering = ["nombre", ]
        get_latest_by = "nombre"

    def __str__(self):
        return f'{self.nombre}'

class TipoContrato(models.Model):
    id_netTime = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        unique=True,
        help_text="Para matchear marcajes e importaciones"
    )
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Tipo de contrato"
        verbose_name_plural = "Tipos de contrato"
        get_latest_by = "id_netTime"

    def __str__(self):
        return f'{self.nombre}'

class Empleado(models.Model):

    ### from nettime webservice ###
    id_netTime = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        unique=True,
        help_text="Para matchear marcajes e importaciones"
    )
    apellido = models.CharField(max_length=20)
    nombre = models.CharField(max_length=20)
    dni = models.CharField(max_length=8, unique=True)
    legajo = models.CharField(max_length=50, null=True, blank=True)
    empresa = models.CharField(max_length=50, null=True, blank=True)
    convenio = models.CharField(max_length=50, null=True, blank=True)

    nro_cuenta = models.CharField(
        "Número de cuenta", max_length=50, null=True, blank=True)
    tipo = models.ForeignKey(
        'TipoContrato', on_delete=models.CASCADE, null=True, blank=True)
    liquidacion = models.ForeignKey(
        'TipoLiquidacion', on_delete=models.CASCADE, null=True, blank=True)

    escala = models.ManyToManyField('Escala')

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        get_latest_by = "dni"
        ordering = ["dni", "apellido", "nombre"]
    
    class ReportBuilder:
        extra = ['legajo_apellido_nombre', ]

    def is_busy(self, fecha, inicio, fin, rec_ignore=None):
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
        )
        
        if rec_ignore:
            clases = clases.exclude(
                #ignore if is editing self object
                recurrencia=rec_ignore
            )

        return clases.exists()

    @classmethod
    def serializable_fields(cls):
        return [field.name for field in cls._meta.fields
            if field.name not in ('id', 'id_netTime') and
                not isinstance(field, models.ForeignKey) and
                not isinstance(field, models.ManyToManyField)
        ]

    @classmethod
    def update_from_nettime(cls):
        """ use pull_netTime() for get all employees from netTime webservice """

        try:
            empleados_nt = utils.pull_netTime(
                "Employee",  # Container
                _fields=[
                    "id", "name", "nameEmployee", "LastName", "companyCode",
                    "employeeCode", "persoTipo", "persoLiq", "persoCuenta",
                ]
            )

            for registro in empleados_nt.get("Employee"):
                try:
                    empleado = cls.objects.get(id_netTime=registro.get("id"))
                except:
                    empleado = cls.objects.create(
                        id_netTime=registro.get("id"))

                #update employee data
                empleado.dni = registro.get("name")
                empleado.apellido = registro.get("LastName")
                empleado.nombre = registro.get("nameEmployee")
                empleado.legajo = registro.get("employeeCode")
                empleado.empresa = registro.get("companyCode")
                empleado.nro_cuenta = registro.get("persoCuenta")
                
                try:  # trying get from id_nettime
                    empleado.tipo = TipoContrato.objects.get(
                        id_netTime=registro.get("persoTipo"))
                    empleado.liquidacion = TipoLiquidacion.objects.get(
                        id_netTime=registro.get("persoLiq"))
                except:
                    pass

                empleado.save()

        except Exception as error:
            raise error
    
    @property
    def pronombre(self):
        return "el"

    @property
    def legajo_apellido_nombre(self):
        return f'{self.legajo} - {self.apellido} {self.nombre}'

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return '{}, {}'.format(
            self.apellido,
            self.nombre if self.nombre else ''
        )

class Sede(models.Model):
    id_netTime = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        unique=True,
        help_text="Para matchear marcajes e importaciones")
    nombre = models.CharField(max_length=100)
    empresa = models.CharField(max_length=100, null=True, blank=True)
    sociedad = models.CharField(max_length=100, null=True, blank=True)

    codigo = models.CharField(max_length=50, blank=True, null=True, unique=True)
    tipo = models.CharField(max_length=30, default="Física", blank=True)

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        get_latest_by = "nombre"
        ordering = ["nombre", ]

    @classmethod
    def update_from_nettime(cls):
        """ use pull_netTime() for get all Sede's from netTime webservice """

        try:
            sedes_nt = utils.pull_netTime(
                "Custom",  # Container
                _fields=["id", "name", "extra_1", "extra_2"],
                _filter='this.type == "sede"'
            )

            for registro in sedes_nt.get("Custom"):
                try:
                    sede = cls.objects.get(id_netTime=registro.get("id"))
                except:
                    sede = cls.objects.create(id_netTime=registro.get("id"))

                #update employee data
                sede.nombre = registro.get("name")
                sede.empresa = registro.get("extra_1")
                sede.sociedad = registro.get("extra_2")
                sede.save()

        except Exception as error:
            raise error

    @property
    def pronombre(self):
        return "la"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return f'{self.nombre}'

class Saldo(models.Model):
    actividad = models.ForeignKey('Actividad', on_delete=models.CASCADE)
    sede = models.ForeignKey('Sede', on_delete=models.CASCADE)
    desde = models.DateField(default=timezone.now)
    hasta = models.DateField(default=timezone.now)
    saldo_asignado = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        help_text="Cantidad de clases que desea disponibilizar")

    #history = HistoricalRecords()

    class Meta:
        verbose_name = "Saldo"
        verbose_name_plural = "Saldos"
        get_latest_by = "-desde"
        ordering = ["-desde", "-hasta"]

    def get_edit_url(self):
        """ construct edit url from current object """
        return reverse('saldo_update', kwargs={"pk": self.id})

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model":self.__class__.__name__, "pk":self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('saldos_view')
    
    @classmethod
    def check_overlap(cls, _sede, _actividad, _desde, _hasta, id_exclude=None):
        """ 
        Informs if a period generates an overlap with one already
        created in right place and activity.
        """

        start_before = Q()
        start_before.add(Q(desde__lte=_desde), Q.AND)
        start_before.add(Q(hasta__gte=_desde), Q.AND)

        start_after = Q()
        start_after.add(Q(desde__gte=_desde), Q.AND)
        start_after.add(Q(desde__lte=_hasta), Q.AND)

        qs = Q()
        qs.add(start_before, Q.OR)
        qs.add(start_after, Q.OR)

        _saldos = cls.objects.filter(
            sede = _sede,
            actividad = _actividad,
        ).filter(qs)

        if id_exclude:
            _saldos = _saldos.exclude(pk=id_exclude)

        return _saldos.count()

    @classmethod
    def check_saldos(cls, _sede, _actividad, _desde, _hasta):
        _saldos = cls.objects.filter(
            sede=_sede,
            actividad=_actividad,
            desde__gte=_desde,
            hasta__lte=_hasta)
        
        #saldo_a_favor
        saf = True if _saldos else False

        for _saldo in _saldos:
            saf = False if _saldo.saldo_disponible < 1 else saf

        return saf

    @property
    def saldo_disponible(self):
        clases = Clase.objects.filter(
            actividad=self.actividad,
            sede=self.sede,
            fecha__gte=self.desde,
            fecha__lte=self.hasta,
        ).exclude(
            estado="5"    #canceladas
        ).count()

        return self.saldo_asignado - clases

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return '{} de {} para {} en {}'.format(
            self.saldo_disponible,
            self.saldo_asignado,
            self.actividad.nombre,
            self.sede.nombre
        )

class Recurrencia(models.Model):
    fecha_desde = models.DateField(default=timezone.now)
    fecha_hasta = models.DateField(blank=True)
    horario_desde = models.TimeField(default=timezone.now)
    horario_hasta = models.TimeField(blank=True)
    empleado = models.ForeignKey(
        'Empleado', on_delete=models.SET_NULL, null=True)
    actividad = models.ForeignKey(
        'Actividad', on_delete=models.SET_NULL, null=True)
    sede = models.ForeignKey('Sede', on_delete=models.SET_NULL, null=True)
    lugar = models.ForeignKey('Lugar', on_delete=models.SET_NULL, null=True)
    weekdays = MultiSelectField(
        'Días de la semana', choices=settings.DIA_SEMANA_CHOICES,
        null=True, blank=True)
    locked = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        verbose_name = "Recurrencia"
        verbose_name_plural = "Recurrencias"
        get_latest_by = "-fecha_desde"
        ordering = ["-fecha_desde", "-fecha_hasta"]

    def get_dias_str(self):
        return ', '.join(utils.get_dia_display(*self.weekdays))
    get_dias_str.short_description = "Días"

    def get_dias_list(self):
        return utils.get_dia_display(*self.weekdays)

    @classmethod
    def check_overlap(cls, employee, weekdays, desde, hasta, hora_ini, \
            hora_end, ignore=None):
        """ informs if a period generates an overlap with one already
            created """
        
        ### dates ###
        start_before = Q()
        start_before.add(Q(fecha_desde__lte=desde), Q.AND)
        start_before.add(Q(fecha_hasta__gte=desde), Q.AND)

        start_after = Q()
        start_after.add(Q(fecha_desde__gte=desde), Q.AND)
        start_after.add(Q(fecha_desde__lte=hasta), Q.AND)

        period = Q()
        period.add(start_before, Q.OR)
        period.add(start_after, Q.OR)
        ### dates ###

        ### hours ###
        onset_before = Q()
        onset_before.add(Q(horario_desde__lte=hora_ini), Q.AND)
        onset_before.add(Q(horario_hasta__gt=hora_ini), Q.AND)

        onset_after = Q()
        onset_after.add(Q(horario_desde__gte=hora_ini), Q.AND)
        onset_after.add(Q(horario_desde__lt=hora_end), Q.AND)

        timelapse = Q()
        timelapse.add(onset_before, Q.OR)
        timelapse.add(onset_after, Q.OR)
        ### hours ###

        ### weekdays ###
        qs_days = Q()
        [qs_days.add(Q(weekdays__contains=day), Q.OR) for day in weekdays]


        _recs = cls.objects.filter(
            empleado=employee,
        ).filter(period).filter(timelapse).filter(qs_days)

        if ignore:
            _recs = _recs.exclude(pk=ignore)

        return _recs.count()

    def get_edit_url(self):
        """ construct edit url from current object """
        return reverse('programacion_update', kwargs={"pk": self.id})

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model":self.__class__.__name__, "pk":self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('programaciones_view')

    @property
    def pronombre(self):
        return "la"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return 'Los {} de {} a {}, desde {} hasta {} para {}'.format(
            self.get_dias_str(),
            self.horario_desde.strftime("%H:%M"),
            self.horario_hasta.strftime("%H:%M"),
            self.fecha_desde, self.fecha_hasta,
            self.empleado
        )

class Clase(models.Model):
    recurrencia = models.ForeignKey(
        'Recurrencia', on_delete=models.CASCADE, null=True)
    creacion = models.DateTimeField(default=timezone.now)

    dia_semana = models.CharField(
        max_length=9, choices=settings.DIA_SEMANA_CHOICES, blank=True)
    fecha = models.DateField(blank=True, default=timezone.now)
    horario_desde = models.TimeField(blank=True, default=timezone.now)
    horario_hasta = models.TimeField(blank=True, default=timezone.now)
    
    horas = models.FloatField(default=0.0)
    horas_nocturnas = models.FloatField(default=0.0)
    horas_diurnas = models.FloatField(default=0.0)

    actividad = models.ForeignKey(
        Actividad, blank=True, null=True, on_delete=models.SET_NULL)
    sede = models.ForeignKey(
        Sede, blank=True, null=True, on_delete=models.SET_NULL)

    empleado = models.ForeignKey(
        Empleado, blank=True, null=True, on_delete=models.SET_NULL,
        related_name='empleado')
    reemplazo = models.ForeignKey(
        Empleado, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='reemplazo')
    ausencia = models.ForeignKey(
        MotivoAusencia, blank=True, null=True, on_delete=models.SET_NULL,
        related_name='ausencia')
    confirmada = models.BooleanField(blank=True, default=False)

    modificada = models.BooleanField(blank=True, default=False)
    estado = models.CharField(
        max_length=1, choices=settings.ESTADOS_CHOICES, null=True, blank=True,
        default=settings.ESTADOS_CHOICES[0][0])
    presencia = models.CharField(
        max_length=12, choices=settings.PRESENCIA_CHOICES, null=True,
        blank=True, default=settings.PRESENCIA_CHOICES[0][0])

    #related comments
    comentarios = GenericRelation('GrupoComentario')

    locked = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = "Clase"
        verbose_name_plural = "Clases"
        get_latest_by = "-fecha"
        ordering = ["-fecha"]

        permissions = [
            ("confirm_classes", "Can confirm classes"),
            ("absence_management", "Can manage absence"),
            ("asign_replacement", "Can assign replacements"),
        ]

    class ReportBuilder:
        # Lists or tuple of excluded fields
        exclude = ('comentarios',)
        # Explicitly allowed fields
        #fields = ('get_dia_semana_display',)
        # List extra fields (useful for methods)
        extra = (
            'monto', 'url_certificados', 'dia_semana_display',
            'format_user_comments',
        )

    def save(self, *args, **kwargs):
        """ Set hours attributes with start and end properties. """

        self.horas = self.get_hours()
        self.horas_nocturnas = self.get_time_intersection(
            settings.HORARIOS_NOCTURNOS)
        self.horas_diurnas = self.horas - self.horas_nocturnas

        super().save(*args, **kwargs)

    @property
    def lugar(self):
        return self.recurrencia.lugar.nombre if self.recurrencia.lugar else ''

    @property
    def ejecutor(self):
        return self.reemplazo if self.reemplazo else self.empleado

    @property
    def user_comments(self):
        return ['[{}, {} ({})]: {}'.format(
            comment.comentario.usuario.last_name,
            comment.comentario.usuario.first_name,
            comment.comentario.fecha.strftime("%d/%m/%Y"),
            comment.comentario.contenido,
        ) for comment in self.comentarios.all()]

    @property
    def format_user_comments(self):
        return '.\r\n'.join(self.user_comments)
    
    @property
    def dia_semana_display(self):
        return self.get_dia_semana_display()

    @property
    def url_certificados(self):
        urls = [cert.complete_file_url for cert in self.certificado_set.all()]
        return '\n'.join(urls)

    @property
    def monto(self):
        #set mount of class
        ejecutor = self.reemplazo if self.reemplazo else self.empleado
        escala = ejecutor.escala.filter(grupo=self.actividad.grupo)
        
        if not escala or not self.horas:
            return 0.0
        
        return round(escala.first().monto_hora * self.horas, 2)

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
        return bool(blocks)

    def get_hours(self):
        """ 
        Return hours of class based on 'horario_hasta' - 'horario_desde'.
        """
        
        fecha = self.fecha
        desde = self.horario_desde
        hasta = self.horario_hasta
        if isinstance(fecha, str):
            fecha = datetime.date.fromisoformat(fecha)
        if isinstance(desde, str):
            desde = datetime.datetime.fromisoformat(f'{fecha} {desde}').time()
        if isinstance(hasta, str):
            hasta = datetime.datetime.fromisoformat(f'{fecha} {hasta}').time()

        hf = datetime.datetime.combine(fecha, hasta)
        hi = datetime.datetime.combine(fecha, desde)

        return round((hf - hi).total_seconds() / 3600, 2)

    def is_time_intersection(self, time_ranges):
        """ Check if class match with a timerange in a tuple of timeranges. """
        
        time_format = "%H:%M"
        
        desde = self.horario_desde
        hasta = self.horario_hasta
        if isinstance(desde, str):
            desde = datetime.datetime.strptime(desde, time_format).time()
        if isinstance(hasta, str):
            hasta = datetime.datetime.strptime(hasta, time_format).time()

        for time_range in time_ranges:
            #recived parameters
            start = datetime.datetime.strptime(time_range[0], time_format)
            end = datetime.datetime.strptime(time_range[1], time_format)

            #class parameters
            cl_ini = datetime.datetime.combine(start.date(), desde)
            cl_end = datetime.datetime.combine(end.date(), hasta)

            #Check overlap
            if cl_ini <= end and cl_end > start:
                return True
        
        return False

    def get_time_intersection(self, time_ranges):
        """ 
        Get hours of class match with a timerange in a tuple of timeranges.
        """

        time_format = "%H:%M"
        total_seconds = 0

        desde = self.horario_desde
        hasta = self.horario_hasta
        if isinstance(desde, str):
            desde = datetime.datetime.strptime(desde, time_format).time()
        if isinstance(hasta, str):
            hasta = datetime.datetime.strptime(hasta, time_format).time()

        for time_range in time_ranges:
            #recived parameters
            start = datetime.datetime.strptime(time_range[0], time_format)
            end = datetime.datetime.strptime(time_range[1], time_format)

            #class parameters
            cl_ini = datetime.datetime.combine(start.date(), desde)
            cl_end = datetime.datetime.combine(end.date(), hasta)

            # get offsets
            diff = min(cl_end, end) - max(cl_ini, start)
            if diff.total_seconds() > 0:
                total_seconds += diff.total_seconds()

        return round(total_seconds / 3600, 2)

    def to_monitor(self):
        """ convert a instance to dict for class monitor """

        return {
            'id': self.id,
            'estado': self.get_estado_display(),
            'was_made': self.was_made,
            'empleado': self.empleado.__str__(),
            'reemplazo': self.reemplazo.__str__() if self.reemplazo else "",
            'sede': self.sede.nombre,
            'actividad': self.actividad.nombre,
            'dia_semana': self.get_dia_semana_display(),
            'fecha': self.fecha,
            'horario_desde': self.horario_desde.strftime("%H:%M"),
            'horario_hasta': self.horario_hasta.strftime("%H:%M"),
            'modificada': self.modificada,
            'ausencia': self.ausencia.__str__() if self.ausencia else "",
            'confirmada': self.confirmada,
            'comentarios': self.comentarios.all().count() if self.comentarios else 0,
        }

    def to_calendar(self):
        return {
            'title': f'{self.actividad.nombre} | {self.ejecutor}',
            'start': datetime.datetime.combine(
                self.fecha, self.horario_desde
            ).replace(second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:00'),
            'end': datetime.datetime.combine(
                self.fecha, self.horario_hasta
            ).replace(second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:00'),
        }

    def update_status(self):
        """ update the class status according to all its variables  """

        if self.fecha > datetime.date.today():
            self.estado = settings.ESTADOS_CHOICES[0][0]    #pendiente

        if self.was_made:
            self.presencia = settings.PRESENCIA_CHOICES[-1][0]
            self.estado = settings.ESTADOS_CHOICES[1][0]    #realizada
        else:
            self.presencia = settings.PRESENCIA_CHOICES[0][0]
            self.estado = settings.ESTADOS_CHOICES[0][0]    #pendiente

        if self.ausencia:
            self.estado = settings.ESTADOS_CHOICES[3][0]    #ausencia

        if self.reemplazo:
            self.estado = settings.ESTADOS_CHOICES[2][0]    #reemplazo

        self.save()
        return self.estado

    @property
    def pronombre(self):
        return "la"

    @property
    def get_str(self):
        return self.__str__()

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model":self.__class__.__name__, "pk":self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('clases_view')

    def __str__(self):

        return '{}, el {} {} de {} a {} para {}'.format(
            self.actividad.nombre,
            self.get_dia_semana_display(),
            self.fecha,
            self.horario_desde.strftime("%H:%M"),
            self.horario_hasta.strftime("%H:%M"),
            self.empleado
        )

# class ClaseReemplazo(models.Model):
#     clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
#     empleado = models.ForeignKey(
#         Empleado, blank=True, null=True, on_delete=models.SET_NULL)
    
#     class Meta:
#         verbose_name = "Reemplazo de Clase"
#         verbose_name_plural = "Reemplazos de Clases"
#         get_latest_by = "id"

class Marcaje(models.Model):
    empleado = models.ForeignKey(
        'Empleado', blank=True, null=True, on_delete=models.SET_NULL)
    usuario = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    fecha = models.DateField(blank=True, default=timezone.now)
    hora = models.TimeField(null=True, blank=True)

    from_nettime = models.BooleanField(blank=True, default=False)
    locked = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = "Marcaje"
        verbose_name_plural = "Marcajes"
        get_latest_by = "-fecha"
        ordering = ["-fecha", "hora"]

    @classmethod
    def update_from_nettime(cls):
        """ Use pull_clockings() for get all clockings of a employee in a 
            specific period.
            Recalculate presence blocks and class status."""

        try:
            #hardcoded now
            start = datetime.datetime(2020, 1, 1, 0, 0)
            end = datetime.datetime.now()
            _type = "Attendance"

            #delta between clockings setting
            _delta = datetime.timedelta(minutes=settings.MINS_BTW_CLOCKS)

            #employees = Empleado.objects.values_list('pk', flat=True)
            employees = Empleado.objects.all()

            for employee in employees:
                marcs = utils.pull_nt_clockings(employee.pk, start, end, _type)
                #hardcoded date
                marc_ant = datetime.datetime.fromisoformat("2001-01-01 00:00")

                for marc in marcs:
                    if marc["Datetime"] - marc_ant >= _delta:
                        #check if exists
                        app_marc = cls.objects.filter(
                            empleado=employee,
                            fecha=marc["Datetime"].date(),
                            hora=marc["Datetime"].time(),
                        )
                        #create if not exists
                        if not app_marc:
                            cls.objects.create(
                                empleado=employee,
                                fecha=marc["Datetime"].date(),
                                hora=marc["Datetime"].time(),
                                from_nettime=True,
                                locked=True,
                            )
                        #update if marc was be processed only
                        marc_ant = marc["Datetime"]

                #recalculate days
                for i in range((end - start).days + 1):
                    _day = start + datetime.timedelta(days=i)
                    BloqueDePresencia.recalcular_bloques(employee, _day.date())

            #update classes status
            clases = Clase.objects.filter(fecha__gte=start, fecha__lte=end)
            [clase.update_status() for clase in clases] if clases else None

        except Exception as error:
            raise error

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def user_can_delete(self, user):
        """ Inform if a user can delete specific clocking. """

        #check delete clockings permissions
        del_perm = user.has_perm('scg_app.delete_marcaje')
        if del_perm and (self.usuario == user or user.is_superuser):
            return True

        return False
    
    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model":self.__class__.__name__, "pk":self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse(
            'gestion_marcajes',
            kwargs={"id_empleado":self.empleado.id, "fecha":self.fecha})

    def __str__(self):
        return f'{self.empleado}, el {self.fecha} a las {self.hora}'

class BloqueDePresencia(models.Model):
    empleado = models.ForeignKey(
        'Empleado', blank=True, null=True, on_delete=models.CASCADE)

    fecha = models.DateField(blank=True, default=timezone.now)

    inicio = models.ForeignKey(
        'Marcaje', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='inicio')
    fin = models.ForeignKey(
        'Marcaje', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='fin')

    class Meta:
        verbose_name = "Bloque de presencia"
        verbose_name_plural = "Bloques de presencia"
        get_latest_by = "-fecha"
        ordering = ["-fecha", "-inicio"]

        permissions = [
            ("recalculate_blocks", "Can recalculate blocks of a specific day"),
        ]

    @classmethod
    def recalcular_bloques(cls, empleado, fecha):
        """ Recalculates an employee's presence blocks on a specific day """

        cls.objects.filter(empleado=empleado, fecha=fecha).delete()

        #grouped
        _day_clockings = Marcaje.objects.filter(
            empleado=empleado, fecha=fecha).order_by('hora')
        if not _day_clockings:
            return True

        if len(_day_clockings) != 1:
            for entrada, salida in utils.grouped(_day_clockings, 2):
                bloque = cls()
                bloque.empleado = empleado
                bloque.inicio = entrada
                bloque.fin = salida
                bloque.fecha = fecha
                bloque.save()

        if len(_day_clockings) % 2:
            last_bloque = cls()
            last_bloque.empleado = empleado
            last_bloque.fecha = fecha
            last_bloque.inicio = _day_clockings.last()
            last_bloque.save()

        return True

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __repr__(self):
        return f'Presencia({self.inicio}, {self.fin})'

    def __str__(self):
        return 'Presencia de {} el {} de {} a {}'.format(
            self.empleado,
            self.fecha,
            self.inicio.hora.strftime("%H:%M") if self.inicio else '-',
            self.fin.hora.strftime("%H:%M") if self.fin else '-')

class Certificado(models.Model):
    """ Can contain an attachment for one or more classes.
        Keep the original motif. """

    clases = models.ManyToManyField('Clase')
    file = models.FileField(
        "Archivo", null=True, blank=True, upload_to='certificados/')
    motivo = models.ForeignKey(
        'MotivoAusencia', blank=True, null=True,
        on_delete=models.SET_NULL, related_name='motivo')

    locked = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        get_latest_by = "locked"
        ordering = ["locked", ]
    
    class ReportBuilder:
        extra = ('complete_file_url',)

    @property
    def complete_file_url(self):
        return '{}://{}{}'.format(
            settings.PROTOCOL,
            settings.BASE_URL,
            self.file.url
        )

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model":self.__class__.__name__, "pk":self.pk})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse(
            'certificados_list',
            kwargs={"id_clase": self.clases.first().id})

    @property
    def pronombre(self):
        return "el"

    @property
    def get_str(self):
        return self.__str__()

    def __str__(self):
        return 'Certificado por {} para {} clases.'.format(
            self.motivo.nombre,
            self.clases.count()
        )

class Liquidacion(models.Model):
    """ Differents file for a specific period. """

    file = models.FileField(
        "Archivo", null=True, blank=True, upload_to='liquidaciones/')
    periodo = models.ForeignKey(Periodo, null=True, on_delete=models.CASCADE)
    
    tipo = models.ForeignKey(
        TipoContrato, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='tipo')

    class Meta:
        verbose_name = "Liquidacion"
        verbose_name_plural = "Liquidaciones"
        get_latest_by = "id"
        ordering = ["-periodo__fecha", "tipo__nombre"]

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model":self.__class__.__name__, "pk":self.pk})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse(
            'periodos_list',
            kwargs={"id_clase": self.clases.first().id})

    @property
    def pronombre(self):
        return "la"

    def __str__(self):
        return 'Liquidación de {} para el periodo {}.'.format(
            self.tipo.nombre,
            str(self.periodo),
        )

class Script(models.Model):
    description = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.description

### user extend ###
User.add_to_class('sedes', models.ManyToManyField(Sede))
User.has_sede_permission = utils.has_sede_permission
User.sedes_available = utils.sedes_available
