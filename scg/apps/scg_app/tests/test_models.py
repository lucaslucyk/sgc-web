# -*- coding: utf-8 -*-

### django ###
from django.test import Client, RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from django.conf import settings
from django.core.files import File

### own ###
from apps.scg_app import models

class PeriodosTest(TestCase):
    
    def setUp(self):
        self.t_types = ('2020-01-01', '2020-03-01', '2020-03-02', '2020-03-31')
        self.t_refer = ('2020-03-01', '2020-03-15', '2020-03-31', '2020-04-01')
        self.no_overlap = (
            ('2020-01-01', '2020-02-29'),
            ('2020-04-01', '2020-04-15'),
        )
        self.locked_days = ('2020-05-01', '2020-05-15', '2020-05-31')
        self.unlocked_days = (
            '2020-02-29', '2020-03-01', '2020-03-15', '2020-03-31',
            '2020-04-01',
        )

        self.period_free = models.Periodo.objects.create(
            desde='2020-03-01',
            hasta='2020-03-31',
            bloqueado=False,
        )
        self.period_locked = models.Periodo.objects.create(
            desde='2020-05-01',
            hasta='2020-05-31',
            bloqueado=True,
        )

    def test_overlap_all(self):
        """
        Test all overlap types:
            - Comming before, on 'desde', between, on 'hasta' and indexed:
                - ending on 'desde'.
                - ending between 'desde' and 'hasta'.
                - ending on 'hasta'.
                - ending after 'hasta'.
        """

        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Periodo.check_overlap(test_type, refer)
                self.assertTrue(is_overlap)

    def test_overlap_excluding(self):
        """ Test all overlaps using exclude_id. """
        
        # excluding bad id
        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Periodo.check_overlap(
                    test_type, refer, id_exclude=self.period_locked.pk)
                self.assertTrue(is_overlap)

        # excluding right id
        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Periodo.check_overlap(
                    test_type, refer, id_exclude=self.period_free.pk)
                self.assertFalse(is_overlap)

    def test_overlap_locked_only(self):
        """ Test all overlaps using locked_only. """

        # ignoring unlockeds
        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Periodo.check_overlap(
                    test_type, refer, locked_only=True)
                self.assertFalse(is_overlap)

        # updating property...
        self.period_free.bloqueado = True
        self.period_free.save()

        # testing again...
        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Periodo.check_overlap(
                    test_type, refer, locked_only=True)
                self.assertTrue(is_overlap)

        # rollback change
        self.period_free.bloqueado = False
        self.period_free.save()

    def test_no_overlap(self):
        """ Test dates what must be pass the test. """

        for dates in self.no_overlap:
            is_overlap = models.Periodo.check_overlap(*dates)
            self.assertFalse(is_overlap)

    def test_locked_days(self):
        """ Test day locked and unlocked (in and out period). """

        for locked in self.locked_days:
            is_locked = models.Periodo.blocked_day(locked)
            self.assertTrue(is_locked)

        for unlocked in self.unlocked_days:
            is_locked = models.Periodo.blocked_day(unlocked)
            self.assertFalse(is_locked)

    def test_get_period_from_date(self):
        """ Test get a period from specific date. """

        periodo = models.Periodo.get_date_period(self.period_free.desde)
        self.assertEqual(self.period_free, periodo)

        periodo = models.Periodo.get_date_period('2020-01-01')
        self.assertFalse(periodo)

    def test_get_url_from_date(self):
        """ Test get a url from date period. """

        url = models.Periodo.get_url_date_period(self.period_free.desde)
        self.assertEqual(self.period_free.get_edit_url(), url)

        url = models.Periodo.get_url_date_period('2020-01-01')
        self.assertEqual(url, '#')

class EmpleadosTest(TestCase):

    def setUp(self):
        self.no_busy = (
            ('09:00', '10:00'),
            ('11:00', '12:00'),
            ('13:00', '14:00'),
        )
        self.busy = (
            ('09:30', '10:30'),
            ('09:30', '11:00'),
            ('09:30', '11:30'),
            ('10:00', '11:00'),
            ('10:00', '11:30'),
            ('10:15', '10:45'),
            ('10:15', '11:00'),
            ('10:15', '11:30'),
        )

        self.empleado = models.Empleado.objects.create(
            apellido='Lucyk',
            nombre='Lucas',
            dni='12345678',
        )

        self.clase = models.Clase.objects.create(
            dia_semana='0',
            fecha='2020-03-15',
            horario_desde='10:00',
            horario_hasta='11:00',
            empleado=self.empleado,
        )

    def test_busy(self):
        """ Test is_busy() method for a instance of Employee. """

        for horarios in self.no_busy:
            busy = self.empleado.is_busy(self.clase.fecha, *horarios)
            self.assertFalse(busy)

        for horarios in self.busy:
            busy = self.empleado.is_busy(self.clase.fecha, *horarios)
            self.assertTrue(busy)


class SaldosTest(TestCase):
    
    def setUp(self):
        self.t_types = ('2020-01-01', '2020-03-01', '2020-03-02', '2020-03-31')
        self.t_refer = ('2020-03-01', '2020-03-15', '2020-03-31', '2020-04-01')
        self.no_overlap = (
            {"_desde": "2020-01-01", "_hasta": "2020-02-29"},
            {"_desde": "2020-04-01", "_hasta": "2020-04-15"},
        )

        self.activity = models.Actividad.objects.create(nombre="T_1")
        self.sede = models.Sede.objects.create(nombre="T_1", id_netTime=1)

        self.activity_two = models.Actividad.objects.create(nombre="T_2")
        self.sede_two = models.Sede.objects.create(nombre="T_2", id_netTime=2)

        self.saldo_one = models.Saldo.objects.create(
            desde='2020-03-01',
            hasta='2020-03-31',
            sede=self.sede,
            actividad=self.activity,
        )
        # second test
        self.saldo_two = models.Saldo.objects.create(
            desde='2020-05-01',
            hasta='2020-05-31',
            sede=self.sede,
            actividad=self.activity,
            saldo_asignado=2,
        )
        self.empleado = models.Empleado.objects.all().first()
        self.clase_one = models.Clase.objects.create(
            dia_semana='0',
            fecha='2020-05-15',
            horario_desde='10:00',
            horario_hasta='11:00',
            empleado=self.empleado,
            sede=self.sede,
            actividad=self.activity,
        )

    def test_overlap_all(self, callback=False):
        """
        Test all overlap types:
            - Comming before, on 'desde', between, on 'hasta' and indexed:
                - ending on 'desde'.
                - ending between 'desde' and 'hasta'.
                - ending on 'hasta'.
                - ending after 'hasta'.
        """

        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Saldo.check_overlap(
                    _sede=self.sede,
                    _actividad=self.activity,
                    _desde=test_type,
                    _hasta=refer,
                )
                self.assertTrue(is_overlap if not callback else not is_overlap)

    def test_overlap_excluding(self):
        """ Test all overlaps using exclude_id. """

        # excluding bad id
        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Saldo.check_overlap(
                    _sede=self.sede,
                    _actividad=self.activity,
                    _desde=test_type,
                    _hasta=refer,
                    id_exclude=self.saldo_two.pk,
                )
                self.assertTrue(is_overlap)

        # excluding right id
        for test_type in self.t_types:
            for refer in self.t_refer:
                is_overlap = models.Saldo.check_overlap(
                    _sede=self.sede,
                    _actividad=self.activity,
                    _desde=test_type,
                    _hasta=refer,
                    id_exclude=self.saldo_one.pk,
                )
                self.assertFalse(is_overlap)
        
    def test_no_overlap(self):
        """ Test dates what must be pass the test. """

        for dates in self.no_overlap:
            is_overlap = models.Saldo.check_overlap(
                _sede=self.sede,
                _actividad=self.activity,
                **dates,
            )
            self.assertFalse(is_overlap)

    def test_no_overlap_changing_values(self):
        """ Test no overlap with another sede and/or activity. """

        # change sede only
        self.sede, self.sede_two = self.sede_two, self.sede
        self.test_overlap_all(callback=True)

        # change sede and activity
        self.activity, self.activity_two = self.activity_two, self.activity
        self.test_overlap_all(callback=True)

        # change activity only
        self.sede, self.sede_two = self.sede_two, self.sede
        self.test_overlap_all(callback=True)

    def test_saldo_actual(self):
        """ Test what values informed are right. """

        # positive default
        self.assertEqual(self.saldo_two.saldo_disponible, 1)
        
        # zero
        self.saldo_two.saldo_asignado = 1
        self.saldo_two.save()
        self.assertEqual(self.saldo_two.saldo_disponible, 0)

        # negative
        self.saldo_two.saldo_asignado = 0
        self.saldo_two.save()
        self.assertEqual(self.saldo_two.saldo_disponible, -1)

        # no classes
        self.assertEqual(self.saldo_one.saldo_disponible, 0)

    def test_saldo_available(self):
        """ Test if have available saldo in a time period. """

        values_test = {
            0: False, # negative available
            1: False, # zero available
            2: True,  # positivive available
        }

        for saldo_asignado, test in values_test.items():
            self.saldo_two.saldo_asignado = saldo_asignado
            self.saldo_two.save()

            checked = models.Saldo.check_saldos(
                _sede=self.saldo_two.sede,
                _actividad=self.saldo_two.actividad,
                _desde=self.clase_one.fecha,
                _hasta=self.clase_one.fecha,
            )

            self.assertEqual(checked, test)

class RecurrenciasTest(TestCase):
    def setUp(self):
        self.weekdays = ["0", "2"]
        self.days_not_included = ["3", "4"]
        self.lugar = models.Lugar.objects.create(
            nombre="Testing Place",
            codigo="TP01",
        )
        self.rec = models.Recurrencia.objects.create(
            fecha_desde="2020-06-01",
            fecha_hasta="2020-06-30",
            horario_desde="05:00",
            horario_hasta="07:00",
            empleado=models.Empleado.objects.first(),
            actividad=models.Actividad.objects.first(),
            sede=models.Sede.objects.first(),
            lugar=self.lugar,
            weekdays=self.weekdays,
        )

        self.test_no_overlap = (
            {"_desde": "2020-05-01", "_hasta": "2020-05-31"},
            {"_desde": "2020-07-01", "_hasta": "2020-07-31"},
        )
        self.test_overlap = (
            {
                "_desde": "2020-05-01",
                "_hasta": [
                    "2020-06-01", "2020-06-15", "2020-06-30", "2020-07-01",
                ]
            },
            {
                "_desde": "2020-06-01",
                "_hasta": [
                    "2020-06-01", "2020-06-15", "2020-06-30", "2020-07-01",
                ]
            },
            {
                "_desde": "2020-06-15",
                "_hasta": [
                    "2020-06-15", "2020-06-30", "2020-07-01",
                ]
            },
            {
                "_desde": "2020-06-30",
                "_hasta": [
                    "2020-06-30", "2020-07-01",
                ]
            },
        )

    def test_get_dias_str(self):
        """ Test if value of get_dias_str is right according to settings. """
        dias_dict = dict(settings.DIA_SEMANA_CHOICES)
        days = ', '.join([dias_dict.get(_) for _ in self.rec.weekdays])

        self.assertEqual(self.rec.get_dias_str(), days)

    def test_get_dias_list(self):
        """ Test if value of get_dias_list is right according to settings. """

        dias_dict = dict(settings.DIA_SEMANA_CHOICES)
        days = [dias_dict.get(_) for _ in self.rec.weekdays]

        self.assertEqual(self.rec.get_dias_list(), days)

    def test_no_overlaps(self):
        """
        Test differents dates and times that should not generate overlap.
        """

        for to_test in self.test_no_overlap:
            value = models.Recurrencia.check_overlap(
                employee=self.rec.empleado,
                weekdays=[self.weekdays[0], ],
                desde=to_test.get("_desde"),
                hasta=to_test.get("_hasta"),
                hora_ini=self.rec.horario_desde,
                hora_end=self.rec.horario_hasta,
            )
            self.assertFalse(value)

        for to_test in self.test_overlap:
            for hasta in to_test.get("_hasta"):
                value = models.Recurrencia.check_overlap(
                    employee=self.rec.empleado,
                    weekdays=[self.weekdays[0],],
                    desde=to_test.get("_desde"),
                    hasta=hasta,
                    hora_ini="10:00",
                    hora_end="11:00",
                )
                self.assertFalse(value)
            
                value = models.Recurrencia.check_overlap(
                    employee=self.rec.empleado,
                    weekdays=[self.days_not_included[0], ],
                    desde=to_test.get("_desde"),
                    hasta=hasta,
                    hora_ini=self.rec.horario_desde,
                    hora_end=self.rec.horario_hasta,
                )
                self.assertFalse(value)

                value = models.Recurrencia.check_overlap(
                    employee=self.rec.empleado,
                    weekdays=[self.weekdays[0], ],
                    desde=to_test.get("_desde"),
                    hasta=hasta,
                    hora_ini=self.rec.horario_desde,
                    hora_end=self.rec.horario_hasta,
                    ignore=self.rec.pk
                )
                self.assertFalse(value)
    
    def test_overlaps(self):
        """
        Test differents dates and times that should generate overlap.
        """

        for to_test in self.test_overlap:
            for hasta in to_test.get("_hasta"):
                value = models.Recurrencia.check_overlap(
                    employee=self.rec.empleado,
                    weekdays=[self.weekdays[0], ],
                    desde=to_test.get("_desde"),
                    hasta=hasta,
                    hora_ini=self.rec.horario_desde,
                    hora_end=self.rec.horario_hasta,
                )
                self.assertTrue(value)


class BloqueDePresenciaTest(TestCase):
    def setUp(self):
        self.entrada = models.Marcaje.objects.create(
            empleado=models.Empleado.objects.first(),
            fecha="2020-06-01",
            hora="05:05",
        )
        self.salida = models.Marcaje.objects.create(
            empleado=models.Empleado.objects.first(),
            fecha="2020-06-01",
            hora="07:10",
        )
    
    def test_no_bloques(self):
        """ Test that there are no blocks. """

        self.assertFalse(models.BloqueDePresencia.objects.all())

    def test_recalculate(self):
        """ Recalculates to test that there are now blocks """

        recalculated = models.BloqueDePresencia.recalcular_bloques(
            empleado=self.entrada.empleado,
            fecha=self.entrada.fecha,
        )
        self.assertTrue(recalculated)
        self.assertTrue(models.BloqueDePresencia.objects.all())

class ClasesTest(TestCase):
    def setUp(self):
        self.VALUES = {
            "HORAS": 2,
            "HORAS_NOC": 1,
            "HORAS_DIUR": 1,
        }
        self.weekdays = ["0", "2"]
        self.lugar = models.Lugar.objects.create(
            nombre="Testing Place",
            codigo="TP01",
        )
        self.empleado = models.Empleado.objects.create(
            apellido='Lucyk',
            nombre='Lucas',
            dni='12345678',
            id_netTime=1,
        )
        self.reemplazo = models.Empleado.objects.create(
            apellido='Test',
            nombre='Test',
            dni='87654321',
            id_netTime=2,
        )
        self.activity_group = models.GrupoActividad.objects.create(
            nombre="G_1"
        )
        self.activity = models.Actividad.objects.create(
            nombre="T_1",
            grupo=self.activity_group,
        )
        self.sede = models.Sede.objects.create(nombre="T_1", id_netTime=1)
        self.rec = models.Recurrencia.objects.create(
            fecha_desde="2020-06-01",
            fecha_hasta="2020-06-30",
            horario_desde="05:00",
            horario_hasta="07:00",
            empleado=self.empleado,
            actividad=self.activity,
            sede=self.sede,
            lugar=self.lugar,
            weekdays=self.weekdays,
        )
        self.clase = models.Clase.objects.create(
            recurrencia=self.rec,
            dia_semana="0",
            fecha="2020-06-01",
            horario_desde=self.rec.horario_desde,
            horario_hasta=self.rec.horario_hasta,
            actividad=self.activity,
            sede=self.sede,
            empleado=self.empleado,
        )
        # creating clockings and presence blocks for recalculate
        self.entrada = models.Marcaje.objects.create(
            empleado=self.empleado,
            fecha="2020-06-01",
            hora="05:05",
        )
        self.salida = models.Marcaje.objects.create(
            empleado=self.empleado,
            fecha="2020-06-01",
            hora="07:10",
        )
        self.no_intersections = (
            ('03:00', '04:00'),
            ('08:00', '09:00'),
        )

        self.intersections = ({
            "range": ('03:00', '05:01'),
            "time": 0.02,
        }, {
            "range": ('03:00', '05:30'),
            "time": 0.5,
        }, {
            "range": ('03:00', '06:00'),
            "time": 1.0,
        }, {
            "range": ('03:00', '07:30'),
            "time": 2.0,
        }, {
            "range": ('06:45', '07:30'),
            "time": 0.25,
        },
        )

    def test_lugar(self):
        """ Test the property to validate the place name. """

        place = self.clase.recurrencia.lugar
        self.assertEqual(self.clase.lugar, place.nombre)

    def test_hours(self):
        """ Test get_hours method and hours attributes. """

        self.assertEqual(self.clase.get_hours(), 2)

        self.assertEqual(self.clase.horas, self.VALUES["HORAS"])
        self.assertEqual(self.clase.horas_nocturnas, self.VALUES["HORAS_NOC"])
        self.assertEqual(self.clase.horas_diurnas, self.VALUES["HORAS_DIUR"])

    def test_ejecutor(self):
        """ Tests that executor considers the replacementt. """

        self.assertEqual(self.clase.ejecutor, self.empleado)

        # update and try again
        self.clase.reemplazo = self.reemplazo
        self.assertEqual(self.clase.ejecutor, self.reemplazo)

        # rollback
        self.clase.reemplazo = None

    def test_is_cancelled(self):
        """ Test the property is_cancelled, force value and trying again. """

        self.assertFalse(self.clase.is_cancelled)

        # update and try again
        self.clase.estado = settings.ESTADOS_CHOICES[-1][0]
        self.assertTrue(self.clase.is_cancelled)
        
        # rollback
        self.estado = settings.ESTADOS_CHOICES[0][0]

    def test_was_made(self):
        """ 
        Test the property was_made, create clockings and presence blocks and \
            try again.
        """

        self.assertFalse(self.clase.was_made)
        models.BloqueDePresencia.recalcular_bloques(
            empleado=self.entrada.empleado,
            fecha=self.entrada.fecha,
        )

        self.assertTrue(self.clase.was_made)

    def test_is_present(self):
        """ Test the property is_cancelled recalculating and trying again. """

        self.assertFalse(self.clase.is_present)
        
        #create clocking and presence block
        models.BloqueDePresencia.recalcular_bloques(
            empleado=self.entrada.empleado,
            fecha=self.entrada.fecha,
        )

        # update status and try again
        self.clase.update_status()
        self.assertTrue(self.clase.is_present)

    def test_is_time_intersection(self):
        """ Test what does not exist intersection between bad times. """

        #for time_range in self.no_intersections:
        self.assertFalse(self.clase.is_time_intersection(self.no_intersections))

    def test_get_time_intersection(self):
        """ Test values returned with bad and right time ranges. """
        
        # no intersections
        time_intersect = self.clase.get_time_intersection(self.no_intersections)
        self.assertEqual(time_intersect, 0.0)

        # intersections
        for values in self.intersections:
            time = self.clase.get_time_intersection([values.get("range"), ])
            self.assertEqual(time, values.get("time"))
        
    def test_monto(self):
        """ Test ammount with and without activity scale. """

        self.assertEqual(self.clase.monto, 0.0)

        # create and assign scale
        self.empleado.escala.create(
            nombre="E_1",
            grupo=self.activity_group,
            monto_hora=50.0,
        )
        self.assertEqual(self.clase.monto, self.clase.horas * 50.0)

    def test_user_comments(self):
        """
        Test returns of user_comments and format_user_comments properties.
        """
        
        # no comments
        self.assertFalse(self.clase.user_comments)
        self.assertFalse(self.clase.format_user_comments)

        # create test comment and try again
        new_comment = models.Comentario.objects.create(
            usuario=User.objects.first(),
            accion=settings.ACCIONES_CHOICES[-1][0],
            contenido="Testing comment")

        #assign comment
        self.clase.comentarios.create(comentario=new_comment)

        self.assertTrue(self.clase.user_comments)
        self.assertTrue(self.clase.format_user_comments)

    def test_url_certificados(self):
        """
        Test return of url_certificados property with and without associated \
            certificates.
        """
        self.assertFalse(self.clase.url_certificados)

        certif = models.Certificado.objects.create(
            #file=File(open('test_login.py', 'r')),
            motivo=models.MotivoAusencia.objects.create(nombre="MA_1")
        )
        certif.clases.add(self.clase)

        self.assertTrue(self.clase.url_certificados)

