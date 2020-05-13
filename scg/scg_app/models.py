# -*- coding: utf-8 -*-

### built-in ###
import os
import datetime
from collections import defaultdict

### third ###
from multiselectfield import MultiSelectField
#from simple_history.models import HistoricalRecords

### django ###
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator    #, MaxValueValidator
from django.shortcuts import reverse
from django.db.models import Q

### own ###
from scg_app import utils
from django.conf import settings

class Periodo(models.Model):
    """ To manage available and blocked periods """

    desde = models.DateField(blank=True)
    hasta = models.DateField(blank=True)
    bloqueado = models.BooleanField(blank=True, default=True)

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ["-desde"]

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
        r_ids = set(clases.values_list('parent_recurrencia__id', flat=True))
        Recurrencia.objects.filter(pk__in=r_ids).update(locked=self.bloqueado)

        ### marcajes ###
        Marcaje.objects.filter(
            fecha__gte=self.desde,
            fecha__lte=self.hasta,
            locked=not self.bloqueado
        ).update(locked=self.bloqueado)

        return clases.count()

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
    monto_hora = models.CharField(max_length=10)

    class Meta:
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"
        get_latest_by = "id"

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

    class Meta:
        verbose_name = "Grupo de Actividad"
        verbose_name_plural = "Grupos de Actividad"
        get_latest_by = "id"

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
        'GrupoActividad', on_delete=models.SET(''), null=True, blank=True)

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        get_latest_by = "id"

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

    class Meta:
        verbose_name = 'Motivo de Ausencia'
        verbose_name_plural = 'Motivos de Ausencia'
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
        get_latest_by = "id_netTime"

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
    legajo = models.CharField(max_length=10, null=True, blank=True)
    empresa = models.CharField(max_length=10, null=True, blank=True)

    tipo = models.ForeignKey(
        'TipoContrato', on_delete=models.CASCADE, null=True, blank=True)
    liquidacion = models.ForeignKey(
        'TipoLiquidacion', on_delete=models.CASCADE, null=True, blank=True)

    escala = models.ManyToManyField('Escala')

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        get_latest_by = "id"

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
            clases.exclude(parent_recurrencia=rec_ignore)

        return clases.exists()

    @classmethod
    def update_from_nettime(cls):
        """ use pull_netTime() for get all employees from netTime webservice """

        try:
            empleados_nt = utils.pull_netTime(
                "Employee",  # Container
                _fields=[
                    "id", "name", "nameEmployee", "LastName", "companyCode",
                    "employeeCode", "persoTipo", "persoLiq",
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
    nombre = models.CharField(max_length=40)
    tipo = models.CharField(max_length=30, default="Física", blank=True)

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        get_latest_by = "id"

    @classmethod
    def update_from_nettime(cls):
        """ use pull_netTime() for get all Sede's from netTime webservice """

        try:
            sedes_nt = utils.pull_netTime(
                "Custom",  # Container
                _fields=["id", "name"],
                _filter='this.type == "sede"'
            )

            for registro in sedes_nt.get("Custom"):
                try:
                    sede = cls.objects.get(id_netTime=registro.get("id"))
                except:
                    sede = cls.objects.create(id_netTime=registro.get("id"))

                #update employee data
                sede.nombre = registro.get("name")
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
        get_latest_by = "id"

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
        """ informs if a period generates an overlap with one already
            created. """

        start_before = Q()
        start_before.add(Q(desde__lte=_desde), Q.AND)
        start_before.add(Q(hasta__gte=_desde), Q.AND)

        start_after = Q()
        start_after.add(Q(desde__gte=_desde), Q.AND)
        start_after.add(Q(desde__lte=_hasta), Q.AND)

        period = Q()
        period.add(start_before, Q.OR)
        period.add(start_after, Q.OR)

        _saldos = cls.objects.filter(
            sede = _sede,
            actividad = _actividad,
        ).filter(period)

        if id_exclude:
            _saldos = _saldos.exclude(pk=id_exclude)

        return _saldos.count()

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
        'Empleado', on_delete=models.SET(''), null=True)
    actividad = models.ForeignKey(
        'Actividad', on_delete=models.SET(''), null=True)
    sede = models.ForeignKey('Sede', on_delete=models.SET(''), null=True)
    weekdays = MultiSelectField(
        'Días de la semana', choices=settings.DIA_SEMANA_CHOICES,
        null=True, blank=True)
    locked = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        verbose_name = "Recurrencia"
        verbose_name_plural = "Recurrencias"
        get_latest_by = "id"

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
    parent_recurrencia = models.ForeignKey(
        'Recurrencia', on_delete=models.CASCADE, null=True)
    creacion = models.DateTimeField(default=timezone.now)
    dia_semana = models.CharField(
        max_length=9, choices=settings.DIA_SEMANA_CHOICES, blank=True)
    fecha = models.DateField(blank=True, default=timezone.now)
    horario_desde = models.TimeField(blank=True, default=timezone.now)
    horario_hasta = models.TimeField(blank=True, default=timezone.now)
    actividad = models.ForeignKey('Actividad', on_delete=models.SET(''))
    sede = models.ForeignKey('Sede', on_delete=models.SET(''))

    empleado = models.ForeignKey(
        'Empleado', on_delete=models.SET(''), related_name='empleado')
    reemplazo = models.ForeignKey(
        'Empleado', blank=True, null=True,
        on_delete=models.SET(''),
        related_name='reemplazo')
    ausencia = models.ForeignKey(
        'MotivoAusencia', blank=True, null=True, on_delete=models.SET(''),
        related_name='ausencia')
    confirmada = models.BooleanField(blank=True, default=False)

    modificada = models.BooleanField(blank=True, default=False)
    estado = models.CharField(
        max_length=1, choices=settings.ESTADOS_CHOICES, null=True, blank=True,
        default=settings.ESTADOS_CHOICES[0][0])
    presencia = models.CharField(
        max_length=12, choices=settings.PRESENCIA_CHOICES, null=True,
        blank=True, default=settings.PRESENCIA_CHOICES[0][0])
    comentario = models.CharField(
        max_length=1000, blank=True, help_text="Aclaraciones varias")

    locked = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = "Clase"
        verbose_name_plural = "Clases"
        get_latest_by = "id"
        ordering = ["-fecha"]

    # class ReportBuilder:
    #     # Lists or tuple of excluded fields
    #     #exclude = ()
    #     # Explicitly allowed fields
    #     fields = ('get_dia_semana_display',)
    #     # List extra fields (useful for methods)
    #     #extra = ('get_dia_semana_display',)

    @property
    def certificados(self):
        cert = Certificado.objects.filter(clases__in=[self])
        return cert    

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

class Marcaje(models.Model):
    empleado = models.ForeignKey('Empleado', on_delete=models.SET(''))
    fecha = models.DateField(blank=True, default=timezone.now)
    hora = models.TimeField(null=True, blank=True)
    locked = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = "Marcaje"
        verbose_name_plural = "Marcajes"
        get_latest_by = "hora"

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
        'Marcaje', blank=True, null=True, on_delete=models.SET(''),
        related_name='inicio')
    fin = models.ForeignKey(
        'Marcaje', blank=True, null=True, on_delete=models.SET(''),
        related_name='fin')

    class Meta:
        verbose_name = "Bloque de presencia"
        verbose_name_plural = "Bloques de presencia"
        ordering = ["-inicio"]

        permissions = [
            ("recalculate_blocks", "Can recalculate blocks of a specific day"),
        ]

    @classmethod
    def recalcular_bloques(cls, empleado, fecha):
        #cls.objects.filter(empleado=empleado, inicio__fecha=fecha).delete()
        cls.objects.filter(empleado=empleado, fecha=fecha).delete()

        #grouped
        _day_clockings = Marcaje.objects.filter(
            empleado=empleado, fecha=fecha).order_by('hora')
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

    #seted in save method and for use in out system (excel, csv, etc)
    file_url = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ["motivo"]

    def save(self, *args, **kwargs):
        self.file_url = '{}://{}{}'.format(
            settings.PROTOCOL,
            settings.BASE_URL,
            self.file.url
        )
        super().save(*args, **kwargs)

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

### user extend ###
User.add_to_class('sedes', models.ManyToManyField(Sede))
