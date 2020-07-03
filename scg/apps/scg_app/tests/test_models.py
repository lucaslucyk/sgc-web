from django.test import Client, RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse

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

    def get_url_from_date(self):
        """ Test get a url from date period. """

        url = models.Periodo.get_url_date_period(self.period_free.desde)
        self.assertEqual(self.period_free.get_edit_url(), url)

        url = models.Periodo.get_date_period('2020-01-01')
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


class ClasesTest(TestCase):
    pass

    

        
