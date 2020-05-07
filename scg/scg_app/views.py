# -*- coding: utf-8 -*-

### built-in ###
from collections import defaultdict
import datetime
import re
import math

### django ###
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from requests.exceptions import ConnectionError, HTTPError
from django.core.paginator import EmptyPage, Paginator
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt

### own ###
from scg_app.forms import *
from scg_app.models import *
from django.contrib import messages
from django.apps import apps
import scg_app.tasks as task_mgmt


@login_required
def certificados_list(request, id_clase: int, context=None):
    """ Lists all the justifications for which files were 
        attached with their corresponding reasons.
    """

    clase = get_object_or_404(Clase, pk=id_clase)
    certificados = Certificado.objects.filter(clases__in=[clase])

    _ids = set()
    for certificado in certificados:
        [_ids.add(clase.id) for clase in certificado.clases.all()]

    clases_impacto = Clase.objects.filter(id__in=_ids)

    context = {
        "certificados": certificados,
        "clase": clase,
        "clases_impacto": clases_impacto,
    }

    return render(request, "apps/scg_app/certificados.html", context)

@login_required
def clase_edit(request, pk, context=None):
    """ It lists all the justifications for which files were attached with 
        their corresponding reasons.
        Does not allow overlap with a different class.
    """

    clase = get_object_or_404(Clase, pk=pk)

    if clase.locked:
        form = ClaseUpdForm(instance=clase)
        context = context or {'form': form}

        messages.error(
            request, 
            "El periodo esta bloqueado y la clase no puede ser editada.")
        return render(request, 'apps/scg_app/clase_edit.html', context)

    if request.method == 'POST':
        form = ClaseUpdForm(request.POST, instance=clase)
        if not form.is_valid():
            messages.error(request, f'Error de formulario.')
            context = context or {'form': ClaseUpdForm(instance=clase)}
            return render(request, 'apps/scg_app/clase_edit.html', context)

        clase = form.save(commit=False)

        if clase.parent_recurrencia:
            if (clase.horario_desde != clase.parent_recurrencia.horario_desde 
                or clase.horario_hasta != clase.parent_recurrencia.horario_hasta
            ):    
                if Empleado.is_busy(clase.empleado, clase.fecha, 
                    clase.horario_desde, clase.horario_hasta, 
                    rec_ignore=clase.parent_recurrencia
                ):
                    messages.error(request, "La edición se superpone con otra clase.")
                    return render(request, 'apps/scg_app/clase_edit.html', context)

                clase.modificada = True
                messages.success(request, f'La clase ha sido modificada como excepción a la serie.')
            else:
                clase.modificada = False
                messages.success(request, f'La clase ha sido modificada.')
        
        clase.save()

        context = context or {'form': form}
        return render(request, 'apps/scg_app/clase_edit.html', context)

    form = ClaseUpdForm(instance=clase)
    context = context or {'form': form}

    return render(request, 'apps/scg_app/clase_edit.html', context)

# Create your views here.
def check_admin(user):
   return user.is_superuser

@login_required
def index(request):
    return render(request, "index.html", {})

def about(request): return render(request, "scg_app/about.html", {})

@login_required
def wiki(request): 
    return render(request, "apps/scg_app/wiki.html", {})

class SafePaginator(Paginator):
    def validate_number(self, number):
        try:
            return super(SafePaginator, self).validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise

class PeriodosList(LoginRequiredMixin, ListView):
    """ List periods providing edit and delete actions. """

    model = Periodo
    template_name = 'apps/scg_app/list/periodos.html'
    context_object_name = 'periodos_list'

    ordering = ['-desde']

class EmpleadosList(LoginRequiredMixin, ListView):
    """ List employees without providing any available action. """

    model = Empleado
    template_name = 'apps/scg_app/list/empleados.html'
    context_object_name = 'empleados_list'

    # paginator_class = SafePaginator
    # paginate_by = 25

    ordering = ['apellido', 'nombre',]

class SaldosList(LoginRequiredMixin, ListView):
    """ List Saldos providing edit and delete actions. """

    model = Saldo
    template_name = 'apps/scg_app/list/saldos.html'
    context_object_name = 'saldos_list'

    ordering = ['-desde', 'sede__nombre', 'actividad__nombre']

class RecurrenciasList(LoginRequiredMixin, ListView):
    """ List Recurrencias providing edit and delete action. """

    model = Recurrencia
    template_name = 'apps/scg_app/list/programaciones.html'
    context_object_name = 'programaciones_list'

    ordering = ['-fecha_desde', '-horario_desde', 'actividad__nombre']

class MotivosAusenciaList(LoginRequiredMixin, ListView):
    """ List MotivosDeAusencia without providing any available action. """
    
    model = MotivoAusencia
    template_name = 'apps/scg_app/list/motivos_ausencia.html'
    context_object_name = 'motivos_list'

    ordering = ['nombre']

@login_required
def periodo_create(request, context=None):
    """ Allows create a Periodo.
        It does not allow the overlap with another already generated.
    """

    form = PeriodoForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    if request.method == 'POST':
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, "apps/scg_app/create/periodo.html", context)

        fields = {
            "desde":datetime.date.fromisoformat(form.cleaned_data.get("desde")),
            "hasta":datetime.date.fromisoformat(form.cleaned_data.get("hasta")),
        }

        ### security dates check ###
        if fields.get("desde") >= fields.get("hasta"):
            messages.error(request, "El fin debe ser mayor al inicio.")
            return render(request, "apps/scg_app/create/periodo.html", context)

        ### overlap checks ###
        is_overlap = Periodo.check_overlap(
            fields.get("desde"), fields.get("hasta"))

        if is_overlap:
            messages.error(request, "El periodo se solapa con uno ya creado.")
            return render(request, "apps/scg_app/create/periodo.html", context)

        ### after of all security checks ###
        new_period = Periodo.objects.create(
            desde=fields.get("desde"),
            hasta=fields.get("hasta"),
            bloqueado=form.cleaned_data.get("bloqueado"),
        )

        #lock or allor related objects
        affecteds = new_period.update_related()

        messages.success(
            request, "Periodo creado. Afecta a {0} clases".format(affecteds))
        return redirect('periodo_update', pk=new_period.id)

    return render(request, "apps/scg_app/create/periodo.html", context)


@login_required
def periodo_update(request, pk, context=None):
    """ Allows updating the data of a Periodo.
        It does not allow the overlap with another already generated.
    """
    periodo = get_object_or_404(Periodo, pk=pk)

    if request.method == 'POST':
        form = PeriodoUpdForm(request.POST, instance=periodo)
        context = context or {'form': form}

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, 'apps/scg_app/create/periodo.html', context)

        periodo = form.save(commit=False)

        if Periodo.check_overlap(
            _desde=periodo.desde,
            _hasta=periodo.hasta,
            id_exclude=periodo.pk
        ):
            messages.error(request,
                           "El periodo se superpone con otro ya creado.")
            return render(request, "apps/scg_app/create/periodo.html", context)

        #after of all checks
        periodo.save()

        #lock or allor related objects
        affecteds = periodo.update_related()

        messages.success(
            request, 
            "Periodo actualizado. Afecta a {0} clases.".format(affecteds)
        )

    form = PeriodoUpdForm(instance=periodo)
    context = {'form': form}

    return render(request, 'apps/scg_app/create/periodo.html', context)

@login_required
def confirm_delete(request, model, pk, context=None):
    """ view to confirm delete an object from a specific model """

    try:
        _model = apps.get_model('scg_app', model)
    except:
        raise Http404(f'No existe el modelo {model}')

    obj = get_object_or_404(_model, pk=pk)

    context = {
        "pronoun": obj.pronombre,
        #convert "ModelName" to "Model name"
        "model": re.sub(
            r'([A-Z])', 
            r' \1', obj.__class__.__name__
            ).replace(' ', '', 1).capitalize(),
        "object": obj
    }

    #check locked property
    try:
        locked = obj.locked
    except:
        locked = False

    if locked:
        messages.error(
            request,
            '{0} {1} pertenece a un periodo bloqueado.'.format(
                context["pronoun"].capitalize(),
                context["model"],
            )
        )
        return render(request, "apps/scg_app/confirm_delete.html", context)


    if request.method == "POST":
        messages.success(request, 'Se ha eliminado {0} {1}.'.format(
            context["pronoun"], context["model"]))
        try:
            success_url = obj.pos_delete_url()
        except:
            success_url = 'index'
        
        obj.delete()
        return redirect(success_url)

    return render(request, "apps/scg_app/confirm_delete.html", context)

@login_required
def saldo_update(request, pk, context=None):
    """ Allows updating the data of a Saldo.
        It does not allow the overlap with another already generated.
    """
    saldo = get_object_or_404(Saldo, pk=pk)
    
    if request.method == 'POST':
        form = SaldoUpdForm(request.POST, instance=saldo)
        context = context or {'form': SaldoUpdForm(instance=saldo)}

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, 'apps/scg_app/create/saldo.html', context)

        saldo = form.save(commit=False)

        if Saldo.check_overlap(
            _sede=saldo.sede,
            _actividad=saldo.actividad,
            _desde=saldo.desde,
            _hasta=saldo.hasta,
            id_exclude=saldo.pk
        ):
            messages.error(request, 
                "El periodo se superpone con otro ya creado.")
            return render(request, "apps/scg_app/create/saldo.html", context)

        #after of all checks
        saldo.save()
        messages.success(request, "Se actualizó el saldo correctamente.")

    form = SaldoUpdForm(instance=saldo)
    context = {'form': form}

    return render(request, 'apps/scg_app/create/saldo.html', context)

@login_required
def generar_saldo(request, context=None):
    """ Allows create a Saldo.
        It does not allow the overlap with another already generated.
    """

    form = SaldoForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    if request.method == 'POST':
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, "apps/scg_app/create/saldo.html", context)

        if Saldo.check_overlap(
            _sede = form.cleaned_data.get("sede"),
            _actividad = form.cleaned_data.get("actividad"),
            _desde = form.cleaned_data.get("desde"),
            _hasta = form.cleaned_data.get("hasta"),
        ):
            messages.error(request, 
                "El periodo se superpone con otro ya creado.")
            return render(request, "apps/scg_app/create/saldo.html", context)

        #after of security checks
        new_saldo = Saldo.objects.create(
            sede = form.cleaned_data.get("sede"),
            actividad = form.cleaned_data.get("actividad"),
            desde = form.cleaned_data.get("desde"),
            hasta = form.cleaned_data.get("hasta"), 
            saldo_asignado = form.cleaned_data.get("saldo_asignado"), 
        )
        messages.success(request, 
            "Se ha generado el saldo para la sede y actividad seleccionada.")
        return redirect('saldo_update', pk=new_saldo.id)

    return render(request, "apps/scg_app/create/saldo.html", context)

@login_required
def programar(request, context=None):
    """ create a Recurrencia and classes with corresponding data """

    form = RecurrenciaForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form, 'search_data': {}}

    if request.method == 'POST':

        search_data = {
            "empleado": request.POST.get('empleados-search'),
            "actividad": request.POST.get('actividades-search'),
            "sede": request.POST.get('sedes-search'),
        }
        context["search_data"] = search_data

        if "empleados-results" and "actividades-results" and "sedes-results" not in request.POST.keys():
                messages.warning(request, "Busque y seleccione los datos en desplegables.")
                return render(request, "apps/scg_app/create/programacion.html", context)

        try:    #process data geted by API
            fields = {
                "empleado": get_object_or_404(
                    Empleado, pk=request.POST.get("empleados-results")),
                "actividad": get_object_or_404(
                    Actividad, pk=request.POST.get("actividades-results")),
                "sede": get_object_or_404(
                    Sede, pk=request.POST.get("sedes-results")),
            }

            #update selected data
            context["empleado_selected"] = fields.get("empleado")
            context["actividad_selected"] = fields.get("actividad")
            context["sede_selected"] = fields.get("sede")
        except:
            messages.error(request, "Error en campos de búsqueda.")
            return render(request, "apps/scg_app/create/programacion.html", context)

        ###validate info and process more data
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, "apps/scg_app/create/programacion.html", context)

        fields.update({
            #"dia_semana": form.cleaned_data["dia_semana"],
            "weekdays": form.cleaned_data["weekdays"],
            "fecha_desde": datetime.date.fromisoformat(form.cleaned_data["fecha_desde"]), 
            "fecha_hasta": datetime.date.fromisoformat(form.cleaned_data["fecha_hasta"]), 
            "horario_desde": form.cleaned_data["horario_desde"].replace(second=0, microsecond=0),
            "horario_hasta": form.cleaned_data["horario_hasta"].replace(second=0, microsecond=0),
        })

        ### dates validate
        if fields["fecha_hasta"] < datetime.date.today() and not settings.DEBUG:
            messages.error(request, "No se pueden programar clases para fechas pasadas.")
            return render(request, "apps/scg_app/create/programacion.html", context)

        if fields["fecha_desde"] >= fields["fecha_hasta"]:
            messages.error(request, "La fecha de fin debe ser mayor a la de inicio.")
            return render(request, "apps/scg_app/create/programacion.html", context)

        if fields["horario_desde"] >= fields["horario_hasta"]:
            messages.error(request, "La hora de fin debe ser mayor a la de inicio.")
            return render(request, "apps/scg_app/create/programacion.html", context)

        if not settings.DEBUG:
            if not Saldo.objects.filter(
                actividad=fields["actividad"], 
                sede=fields["sede"], 
                desde__lte=fields["fecha_desde"],
                hasta__gte=fields["fecha_hasta"]
            ).exists():
                messages.error(request, f'No hay saldos para la actividad en la sede seleccionada.')
                return render(request, "apps/scg_app/create/programacion.html", context)

        #check if overlaps with another exist rec
        overlays = Recurrencia.check_overlap(
            employee = fields["empleado"],
            weekdays = fields["weekdays"],
            desde = fields["fecha_desde"],
            hasta = fields["fecha_hasta"],
            hora_ini = fields["horario_desde"],
            hora_end = fields["horario_hasta"]
        )
        if overlays:
            messages.error(request, f'La programación se superpone con {overlays} ya creada/s.')
            return render(request, "apps/scg_app/create/programacion.html", context)

        #after of security checks
        rec = Recurrencia.objects.create(
            weekdays=fields["weekdays"], 
            fecha_desde=fields["fecha_desde"], 
            fecha_hasta=fields["fecha_hasta"], 
            horario_desde=fields["horario_desde"], 
            horario_hasta=fields["horario_hasta"], 
            empleado=fields["empleado"], 
            actividad=fields["actividad"], 
            sede=fields["sede"],
        )

        _not_success, _rejecteds, _creadas = False, False, 0

        for dia in fields["weekdays"]:
            success, rejected, cant_creadas = generar_clases(fields, dia, rec)

            #update status vars
            _not_success = True if not success else _not_success
            _rejecteds = True if rejected != 0 else _rejecteds

        #checks saldos
        if not Saldo.check_saldos(
            fields["sede"], fields["actividad"], 
            fields["fecha_desde"], fields["fecha_hasta"]
        ):
            messages.warning(request, 'Ya no dispone de saldo en periodos puntuales.')

        if _not_success:
            messages.warning(request, 'Programación creada pero no se crearon clases puntuales.')
        elif _rejecteds:
            messages.warning(request, 
                'No se crearon algunas clases porque el empleado no estaba disponible ciertos días y horarios.'
            )

        messages.success(request, "Programación generada!")

    return render(request, "apps/scg_app/create/programacion.html", context)

@login_required
def programacion_update(request, pk, context=None):
    """ update a Recurrencia and classes with corresponding data """

    old_rec = get_object_or_404(Recurrencia, pk=pk)
    rec = get_object_or_404(Recurrencia, pk=pk)

    form = RecurrenciaUpdForm(instance=rec)
    context = {
        "form": form,
        "empleado": rec.empleado,
        "actividad": rec.actividad,
        "sede": rec.sede,
    }
    
    if request.method == 'POST':
        form = RecurrenciaUpdForm(request.POST, instance=rec)
        context["form"] = form

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, 'apps/scg_app/create/programacion.html', context)

        ### dates and times validate
        fields = {
            "fecha_desde": datetime.date.fromisoformat(form.cleaned_data.get("fecha_desde")),
            "fecha_hasta": datetime.date.fromisoformat(form.cleaned_data.get("fecha_hasta")),
            "horario_desde": form.cleaned_data.get("horario_desde").replace(second=0, microsecond=0),
            "horario_hasta": form.cleaned_data.get("horario_hasta").replace(second=0, microsecond=0),
            "weekdays": form.cleaned_data.get("weekdays"),
            "empleado": rec.empleado,
            "actividad": rec.actividad,
            "sede": rec.sede,
        }
        
        if fields.get("fecha_hasta") < datetime.date.today() and not settings.DEBUG:
            messages.error(request, "No se pueden programar clases para fechas pasadas.")
            return render(request, "apps/scg_app/update/programacion.html", context)

        if fields.get("fecha_desde") >= fields.get("fecha_hasta"):
            messages.error(request, "La fecha de fin debe ser mayor a la de inicio.")
            return render(request, "apps/scg_app/update/programacion.html", context)

        if fields.get("horario_desde") >= fields.get("horario_hasta"):
            messages.error(request, "La hora de fin debe ser mayor a la de inicio.")
            return render(request, "apps/scg_app/update/programacion.html", context)

        if fields.get("fecha_desde") < old_rec.fecha_desde:
            messages.error(request, "No se puede extender una programación hacia atrás.")
            return render(request, "apps/scg_app/update/programacion.html", context)

        overlays = Recurrencia.check_overlap(
            employee = rec.empleado,
            weekdays = form.cleaned_data.get("weekdays"),
            desde = form.cleaned_data.get("fecha_desde"),
            hasta = form.cleaned_data.get("fecha_hasta"),
            hora_ini = form.cleaned_data.get("horario_desde"),
            hora_end = form.cleaned_data.get("horario_hasta"),
            ignore = rec.id,
        )

        if overlays:
            messages.error(request, f'La programación se superpone con {overlays} ya creada/s.')
            return render(request, "apps/scg_app/update/programacion.html", context)

        ### dates actions ###
        if fields.get("fecha_hasta") < old_rec.fecha_hasta: #delete end differences
            Clase.objects.filter(parent_recurrencia=old_rec, 
                fecha__gt=fields.get("fecha_hasta")
            ).delete()

        if fields.get("fecha_desde") > old_rec.fecha_desde: #delete coming differences
            Clase.objects.filter(parent_recurrencia=old_rec, 
                fecha__lt=fields.get("fecha_desde")
            ).delete()

        ### weekdays actions ###
        if fields.get("weekdays") != old_rec.weekdays:
            to_delete = list(set(old_rec.weekdays) - set(fields.get("weekdays")))
            Clase.objects.filter(parent_recurrencia=old_rec, dia_semana__in=to_delete).delete()

        ### time actions ###
        exis_overlaps_classes = False
        if (fields.get("horario_desde") != old_rec.horario_desde 
            or fields.get("horario_hasta") != old_rec.horario_hasta
        ):
            clases_to_edit = Clase.objects.filter(parent_recurrencia=old_rec)
            for clase in clases_to_edit:
                if not clase.empleado.is_busy(
                    clase.fecha, clase.horario_desde, 
                    clase.horario_hasta, rec_ignore=rec
                ):
                    clase.horario_desde = fields.get("horario_desde")
                    clase.horario_hasta = fields.get("horario_hasta")
                    clase.save()
                else:
                    exis_overlaps_classes = True
        if exis_overlaps_classes:
            messages.warning(request, "No se pudo editar una o más clases por falta de disponibilidad")

        ### create differences ###
        _not_success, _rejecteds, _creadas = False, False, 0
        for dia in fields["weekdays"]:
            success, rejected, cant_creadas = generar_clases(fields, dia, rec, editing=True)

            #update status vars
            _not_success = True if not success else _not_success
            _rejecteds = True if rejected != 0 else _rejecteds

        #checks saldos
        if not Saldo.check_saldos(
            fields["sede"], fields["actividad"], 
            fields["fecha_desde"], fields["fecha_hasta"]
        ):
            messages.warning(request, 'Ya no dispone de saldo en periodos puntuales.')

        ### Recurrencia update ###
        ### after of all security checks
        rec.weekdays = fields.get("weekdays")
        rec.fecha_desde = fields.get("fecha_desde")
        rec.fecha_hasta = fields.get("fecha_hasta")
        rec.horario_desde = fields.get("horario_desde")
        rec.horario_hasta = fields.get("horario_hasta")
        rec.save()

        #after of all checks
        #saldo.save()
        messages.success(request, "Programación actualizada.")

    return render(request, "apps/scg_app/update/programacion.html", context)

def generar_clases(_fields, _dia, _recurrencia, editing=None):
    """ create, if possible, all classes in the indicated period """

    success, rejected, cant_creadas = True, 0, 0 

    try:
        #+1 for process all days
        num_dias = (_fields["fecha_hasta"] - _fields["fecha_desde"]).days + 1
        #print(num_dias)

        for i in range(num_dias):
            dia_actual = _fields["fecha_desde"] + datetime.timedelta(days=i)

            #print(str(dia_actual.weekday()), str(_dia))

            if str(dia_actual.weekday()) == str(_dia):
                if not _fields["empleado"].is_busy(
                    dia_actual, 
                    _fields["horario_desde"], 
                    _fields["horario_hasta"],
                    rec_ignore=_recurrencia if editing else None
                    ):

                    Clase.objects.create(
                        parent_recurrencia = _recurrencia,
                        dia_semana = _dia,
                        fecha = dia_actual,
                        horario_desde = _fields["horario_desde"],
                        horario_hasta = _fields["horario_hasta"],
                        actividad = _fields["actividad"],
                        sede = _fields["sede"],
                        empleado = _fields["empleado"],
                    )
                    cant_creadas += 1
                else:
                    rejected += 1
    except:
        success = False

    return success, rejected, cant_creadas

class ClasesView(LoginRequiredMixin, ListView):
    model = Clase
    template_name = 'apps/scg_app/monitor_clases.html'
    context_object_name = 'clases_list'

    paginator_class = SafePaginator
    paginate_by = 10

    #ordering = ['fecha']
    results_per_page = 10

    def post(self, request, *args, **kwargs):
        """ return json format for ajax request """

        self.results_per_page = int(request.POST.get('rpp')) or self.results_per_page
        #print(request.POST.get('rpp'))

        form = FiltroForm(request.POST)
        if not form.is_valid():
            messages.warning(self.request, "Datos no válidos.")
            return JsonResponse({"error": "error on form"})

        ### get form data ###
        ## searchs
        data_emple = form.cleaned_data.get('empleado')
        data_reemplazo = form.cleaned_data.get('reemplazo')
        data_actividad = form.cleaned_data.get('actividad')

        # select
        dia_semana = form.cleaned_data.get('dia_semana')
        estado = form.cleaned_data.get('estado')
        motivo_ausencia = form.cleaned_data.get('motivo_ausencia')
        sede = form.cleaned_data.get('sede')

        #times
        dia_inicio = form.cleaned_data.get('dia_inicio')
        dia_fin = form.cleaned_data.get('dia_fin')
        hora_inicio = form.cleaned_data.get('hora_inicio')
        hora_fin = form.cleaned_data.get('hora_fin')

        ### checks ###
        solo_ausencia = form.cleaned_data.get('solo_ausencia')
        solo_reemplazos = form.cleaned_data.get('solo_reemplazos')
        
        #for don't create specific keys
        querys = defaultdict(Q)

        ### searchs ###
        if data_emple or data_reemplazo:
            _fields = ('apellido', 'nombre', 'dni', 'legajo', 'empresa', 
                'tipo__nombre', 'liquidacion__nombre'
            )
            for field in _fields:
                #if data_emple:
                for data in data_emple.split():
                    querys["empleado"].add(Q(**{
                        f'empleado__{field.name}__icontains': data
                    }), Q.OR)
                #if data_reemplazo:
                for data in data_reemplazo.split():
                    querys["reemplazo"].add(Q(**{
                        f'reemplazo__{field.name}__icontains': data
                    }), Q.OR)

        #if data_actividad:
        for data in data_actividad.split():
            querys["actividad"].add(Q(**{
                f'actividad__nombre__icontains': data
            }), Q.OR)
            querys["actividad"].add(Q(**{
                f'actividad__grupo__nombre__icontains': data
            }), Q.OR)

        ### selects ###
        if dia_semana:
            querys["dia_semana"] = Q(dia_semana=dia_semana)
        if estado:
            querys["estado"] = Q(estado=estado)
        if motivo_ausencia:
            querys["motivo_ausencia"] = Q(ausencia=motivo_ausencia)
        if sede:
            querys["sede"] = Q(sede=sede)

        ### times ###
        if dia_inicio:
            querys["dia_inicio"] = Q(fecha__gte=dia_inicio)
        if dia_fin:
            querys["dia_fin"] = Q(fecha__lte=dia_fin)
        if hora_inicio != datetime.time(0, 0):
            querys["hora_inicio"] = Q(horario_hasta__gte=hora_inicio)
        if hora_fin != datetime.time(23, 59):
            querys["hora_fin"] = Q(horario_desde__lt=hora_fin)

        ### checks ###
        if solo_ausencia:
            querys["solo_ausencia"] = Q(ausencia__isnull=not solo_ausencia)
        if solo_reemplazos:
            querys["solo_reemplazos"] = Q(reemplazo__isnull=not solo_reemplazos)

        #get ordering data
        order_by = request.POST.get('order_by', None)
        order_by = [_order.replace("order_", "", 1) for _order in order_by.split(",")] if order_by else None
        order_by = order_by if order_by else ('fecha',)

        #add all the filters with and critery
        query = Q()
        [query.add(v, Q.AND) for k, v in querys.items()]
        qs = Clase.objects.filter(query).order_by(*order_by)

        total_regs = qs.count()

        #get page data
        try:
            page = int(request.POST.get('page'))
        except:
            page = 1

        reg_ini = (page - 1) * self.results_per_page
        reg_end = page * self.results_per_page

        #security validate
        reg_ini = 0 if reg_ini > total_regs else reg_ini
        reg_end = total_regs if reg_end > total_regs else reg_end

        #return corresponding page
        qs = qs[reg_ini:reg_end]

        #list of dict for JsonResponse
        results = [{
            'id': clase.id,
            'estado': clase.get_estado_display(),
            'was_made': clase.was_made,
            'empleado': clase.empleado.__str__(),
            'reemplazo': clase.reemplazo.__str__() if clase.reemplazo else "",
            'sede': clase.sede.nombre,
            'actividad': clase.actividad.nombre,
            'dia_semana': clase.get_dia_semana_display(),
            'fecha': clase.fecha,
            'horario_desde': clase.horario_desde.strftime("%H:%M"),
            'horario_hasta': clase.horario_hasta.strftime("%H:%M"),
            'modificada': clase.modificada,
            'ausencia': clase.ausencia.__str__() if clase.ausencia else "",
            'confirmada': clase.confirmada,
        } for clase in qs]

        return JsonResponse({
            "results": results,
            "pages": math.ceil(total_regs/self.results_per_page),
            "page": page
        })


    def get_queryset(self):
        qs = Clase.objects.filter(fecha__gte=datetime.date.today()).order_by('fecha')
        return qs

    def get_context_data(self, *args, **kwargs):     
        context = super().get_context_data(*args, **kwargs)
        context["form"] = context.get("form") or FiltroForm(self.request.POST if self.request.method == 'POST' else None)
        return context

@login_required
def action_process(request, context=None):
    """ processes the action that was selected 
        to redirect to the corresponding section """

    def get_ids(_keys):
        """ returns a list of ids that were selected """
        _ids = [str(_id.split("_")[-1]) for _id in _keys if "toProcess" in _id]
        return _ids

    if request.method == 'POST':
        _accion = request.POST.get('accion_a_ejecutar')
        ids = get_ids(request.POST.keys())

        if not ids:
            messages.error(request, "Debe seleccionar uno o más registros para ejecutar una acción.")
            return redirect('clases_view')

        ### actions ###
        if _accion == 'ver_certificados':
            if len(ids) != 1: 
                messages.error(request, "Debe seleccionar solo un registro para editarlo.")
                return redirect('clases_view')
            return redirect('certificados_list', id_clase=ids[0])

        if _accion == 'editar_clases':
            if len(ids) != 1: 
                messages.error(request, "Debe seleccionar solo un registro para editarlo.")
                return redirect('clases_view')
            return redirect('clase_update', pk=ids[0])

        if _accion == 'gestion_ausencia':
            return redirect('gestion_ausencia', ids_clases='-'.join(ids))

        if _accion == 'asignar_reemplazo':
            if len(ids) != 1: 
                messages.error(request, "Debe seleccionar solo un registro para asignar un reemplazo.")
                return redirect('clases_view')
            return redirect('asignar_reemplazo', id_clase=ids[0])

        if _accion == 'confirmar_clases':
            return confirmar_clases(request, ids)

        if _accion == 'gestion_recurrencia':
            if len(ids) != 1:
                messages.error(request, "Debe seleccionar solo una clase para gestionar su programación.")
                return redirect('clases_view')

            # get the class if all verifications were correct
            clase = get_object_or_404(Clase, pk=ids[0])

            return redirect('programacion_update', pk=clase.parent_recurrencia.id)

        if _accion == 'gestion_marcajes':
            if len(ids) != 1:
                messages.error(request, "Debe seleccionar solo una clase para ver los marcajes del día.")
                return redirect('clases_view')

            # get the class if all verifications were correct
            clase = get_object_or_404(Clase, pk=ids[0])
            return redirect('gestion_marcajes', id_empleado=clase.empleado.id, fecha=clase.fecha)

    # if accessed by url or method is not POST
    messages.error(request, "Acción o método no soportado.")
    return redirect('clases_view')

def confirmar_clases(request, _ids=None, context=None):
    """ confirm all classes from the ids list """

    if not _ids:
        return render(request, "apps/scg_app/clases_confirm.html", context)

    clases = Clase.objects.filter(pk__in=_ids)
    _success, _error = ([], [])

    # if not clases:
    #     return _success, _ids

    for clase in clases:
        #check if class is not cancelled
        if clase.is_cancelled or clase.locked:
            _error.append(clase)
        else:  
            clase.confirmada = True
            clase.save()
            _success.append(clase)

    if _success:
        messages.success(
            request, 
            'Se {0} {1} {2}.'.format(
                "confirmaron" if len(_success) > 1 else "confirmó",
                    len(_success),
                "clases" if len(_success) > 1 else "clase",
            )
        )
    
    if _error:
        messages.error(
            request, 
            'No se {0} confirmar {1} clase{2} porque esta{3} bloqueada{2} o cancelada{2}.'.format(
                "pudieron" if len(_error) > 1 else "pudo",
                len(_error),
                "s" if len(_error) > 1 else "",
                "n" if len(_error) > 1 else "",
            )
        )

    context = {
        "classes_success": _success,
        "classes_error": _error,
    }
    return render(request, "apps/scg_app/clases_confirm.html", context)

@login_required
def gestion_ausencia(request, ids_clases=None, context=None):
    """
        Permite asignar un motivo, adjunto y un comentario para una clase.
        Si éste recibe un adjunto, crea un Certificado con el archivo y motivo seleccionado.
    """

    #in errors only
    if not ids_clases:
        return render(request, "apps/scg_app/gestion_ausencia.html", context)

    if request.method == 'POST':
        form = MotivoAusenciaForm(request.POST, request.FILES)
    else:
        form = MotivoAusenciaForm()
    
    context = context or {'form': form}

    clases_to_edit = Clase.objects.filter(pk__in=ids_clases.split('-'))

    #lockeds ignore
    lockeds = clases_to_edit.filter(locked=True).count()
    if lockeds:
        messages.warning(
            request, 
            "{0} clase{1} esta{2} bloqueada{1} y fue{3} ignorada{1}.".format(
                lockeds,
                "s" if lockeds > 1 else "",
                "n" if lockeds > 1 else "",
                "ron" if lockeds > 1 else "",
            )
        )
        clases_to_edit = clases_to_edit.exclude(locked=True)

    #if not exists classes to apply
    if not clases_to_edit:
        return render(request, "apps/scg_app/gestion_ausencia.html", context)

    context["clases_to_edit"] = clases_to_edit

    if request.method == 'POST':
        if not form.is_valid():
            messages.error(request, "Error de formulario.")
            return render(request, "apps/scg_app/gestion_ausencia.html", context)

        motivo_ausencia = form.cleaned_data["motivo"]
        adjunto = form.cleaned_data["adjunto"]

        #if a file was added
        if adjunto:
            certif = Certificado.objects.create(file=adjunto, motivo=motivo_ausencia)
            certif.clases.set(clases_to_edit)

        #assign absence for each class
        for clase in clases_to_edit:
            clase.ausencia = motivo_ausencia
            clase.save()
            clase.update_status()

        messages.success(request, "Acción finalizada.")

    return render(request, "apps/scg_app/gestion_ausencia.html", context)

@login_required
def asignar_reemplazo(request, id_clase=None, context=None):
    """ Allows assign and delete a replacement to a class. """

    if not id_clase:
        return render(request, "apps/scg_app/gestion_reemplazo.html", context)

    context = context or {'search_data': {}}

    clase_to_edit = get_object_or_404(Clase, pk=id_clase)
    context["clase_to_edit"] = clase_to_edit

    if request.method == 'POST':
        
        context["search_data"] = {
            "empleado": request.POST.get('empleados-search'),
        }

        if request.POST.get("empleados-results"):
            try:
                reemplazante = get_object_or_404(
                    Empleado, pk=request.POST.get("empleados-results")
                )
                context["reemplazo_selected"] = reemplazante
            except:
                messages.error(request, "Error en campos de búsqueda.")
                return render(request, "apps/scg_app/gestion_reemplazo.html", context)
        else:
            reemplazante = None

        if not reemplazante:
            clase_to_edit.reemplazo = None
            clase_to_edit.save()
            clase_to_edit.update_status()
            messages.success(request, "Se ha borrado el reemplazo.")
            return render(request, "apps/scg_app/gestion_reemplazo.html", context)

        if clase_to_edit.empleado == reemplazante:
            messages.error(request, "El reemplazante no puede ser el empleado asignado.")
            return render(request, "apps/scg_app/gestion_reemplazo.html", context)

        if reemplazante.is_busy(fecha=clase_to_edit.fecha, 
                                inicio=clase_to_edit.horario_desde, 
                                fin=clase_to_edit.horario_hasta
        ):
            messages.error(request, "El reemplazante no está disponible en el rango horario de esta clase.")
            return render(request, "apps/scg_app/gestion_reemplazo.html", context)

        clase_to_edit.reemplazo = reemplazante
        clase_to_edit.save()
        clase_to_edit.update_status()

        messages.success(request, "Reemplazo cargado con éxito!")

    return render(request, "apps/scg_app/gestion_reemplazo.html", context)

@login_required
def gestion_marcajes(request, id_empleado=None, fecha=None, context=None):
    """  
        It shows the classes of the day of an employee and allows adding and removing markings. 
        It is also possible to recalculate the managed day.
    """

    form = MarcajeForm(request.POST if request.method == "POST" else None)
    context = context or {'form': form}

    try:
        id_empleado = int(id_empleado)
        fecha = datetime.date.fromisoformat(fecha)
    except:
        messages.error(request, "Error en parámetros recibidos")
        return render(request, "apps/scg_app/gestion_marcajes.html", context)

    empleado = Empleado.objects.filter(pk=id_empleado)
    if not empleado:
        messages.error(request, "El empleado no existe")
        return render(request, "apps/scg_app/gestion_marcajes.html", context)

    empleado = empleado.first() #checked what exists
    day_classes = Clase.objects.filter(
        empleado__pk=id_empleado, fecha=fecha
    ).order_by('horario_desde')
    day_blocks = BloqueDePresencia.objects.filter(
        empleado__pk=id_empleado, fecha=fecha
    ).order_by('inicio__hora')

    context["day_classes"] = day_classes
    context["day_blocks"] = day_blocks
    #context["day_clockings"] = day_clockings

    if request.method == 'POST':

        if 'recalcular' in request.POST:
            # recalculate blocks
            if not BloqueDePresencia.recalcular_bloques(empleado, fecha):
                messages.error(request, "Hubo un error recalculando el día.")
                return render(request, "apps/scg_app/gestion_marcajes.html", context)

            #update status
            [clase.update_status() for clase in day_classes]

            day_blocks = BloqueDePresencia.objects.filter(
                empleado__pk=id_empleado, fecha=fecha
            ).order_by('inicio')
            context["day_blocks"] = day_blocks
            messages.success(request, "Se recalcularon las clases y bloques del día.")
            return render(request, "apps/scg_app/gestion_marcajes.html", context)

        #check valid form
        if not form.is_valid():
            messages.error(request, "Error de formulario.")
            return render(request, "apps/scg_app/gestion_marcajes.html", context)

        if not form.cleaned_data["hora_marcaje"]:
            messages.error(request, "Ingrese un horario para agregar el marcaje.")
            return render(request, "apps/scg_app/gestion_marcajes.html", context)

        hora_marcaje = form.cleaned_data["hora_marcaje"].replace(second=0)

        #marc_exists = Marcaje.objects.filter(hora=hora_marcaje)
        if Marcaje.objects.filter(fecha=fecha, hora=hora_marcaje, empleado=empleado):   #clocking exists
            messages.error(request, "Ya existe un marcaje en este horario.")
            return render(request, "apps/scg_app/gestion_marcajes.html", context)

        
        try:    #trying save cloocking
            nuevo_marcaje = Marcaje()
            nuevo_marcaje.empleado = empleado
            nuevo_marcaje.fecha = fecha
            nuevo_marcaje.hora = hora_marcaje
            nuevo_marcaje.save()
        except:
            messages.error(request, "Hubo un error agregando el marcaje.")
            return render(request, "apps/scg_app/gestion_marcajes.html", context)

        # recalculate blocks
        if not BloqueDePresencia.recalcular_bloques(empleado, fecha):
            messages.error(request, "Hubo un error recalculando el día.")
            return render(request, "apps/scg_app/gestion_marcajes.html", context)

        #update status
        [clase.update_status() for clase in day_classes]

        #refresh context
        day_blocks = BloqueDePresencia.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('inicio')
        context["day_blocks"] = day_blocks
        messages.success(request, "El marcaje se ha agregado y el día se ha recalculado correctamente.")

    return render(request, "apps/scg_app/gestion_marcajes.html", context)

###################
### front pulls ###
###################

@user_passes_test(check_admin)
def get_nt_empleados(request, context=None):
    """ use pull_netTime() for get all employees from netTime webservice """

    try: 
        Empleado.update_from_nettime()  # internal method
        messages.success(request, "Se actualizaron los empleados desde netTime.")

    except ConnectionError:
        messages.error(request, "No se pudo establecer conexión con el servidor de netTime.")

    except Exception as error:
        messages.error(request, f"{error}")

    return redirect('empleados_view')

@user_passes_test(check_admin)
def get_nt_sedes(request, context=None):
    """ use pull_netTime() for get all Sede's from netTime webservice """

    try:
        Sede.update_from_nettime()  # internal method
        messages.success(request, "Se actualizaron las sedes desde NetTime.")

    except ConnectionError:
        messages.error(request, "No se pudo establecer conexión con el servidor de netTime.")

    except Exception as error:
        messages.error(request, f"{error}")

    return redirect('index')


@user_passes_test(check_admin)
def get_nt_incidencias(request, context=None):
    """ use pull_netTime() for get all MotivoAusencia's from netTime webservice """

    try:
        MotivoAusencia.update_from_nettime()
        messages.success(request, "Se actualizaron los motivos de ausencia desde NetTime.")

    except ConnectionError:
        messages.error(
            request, "No se pudo establecer conexión con el servidor de netTime.")

    except Exception as error:
        messages.error(request, f"{error}")

    return redirect('motivos_ausencia_view')

@user_passes_test(check_admin)
def get_nt_marcajes(request, context=None):
    """ use pull_clockings() for get all clockings of a employee in a 
        specific period.
    """
    try:
        Marcaje.update_from_nettime()   #internal method
        messages.success(request, "Se importaron marcajes desde NetTime.")

    except ConnectionError:
        messages.error(
            request, 
            "No se pudo establecer conexión con el servidor de netTime."
        )

    except Exception as error:
        messages.error(request, f"{error}")

    return redirect('clases_view')

###################
### tasks  mgmt ###
###################

@csrf_exempt
@user_passes_test(check_admin)
def tasks_management(request, context=None):
    """ list and manage import tasks """
    context = context or {'tasks': []}

    tasks = [
        {
            'name': 'SGC - NetTime Sync',
            'task_name': 'sgc_nettime_sync',
            'installed': False,
            'Path': '',
            'State': '',
            'LastRunTime':'',
        },
    ]

    for task in tasks:
        task_def = task_mgmt.task_get_data(task.get('task_name'))
        
        if task_def:
            task['installed'] = True
            task.update(task_def)

    if request.method == 'POST':
        actions = {
            'task_enable': task_mgmt.task_enable,
            'task_disable': task_mgmt.task_disable,
            'task_run': task_mgmt.task_run,
            'task_delete': task_mgmt.task_delete,
            'task_create': task_mgmt.task_create,
        }
        
        try:
            actions.get(request.POST.get('command'))(
                request.POST.get('task_name')
            )
            return JsonResponse({"success": True})

        except Exception as error:
            return JsonResponse({"error": str(error)})

    context['tasks'] = tasks

    return render(request, "tasks/tasks_management.html", context)

### from tbs ###
# def register(request):
#     form = SignUpForm()
#     context = {'form': form}
#     if request.method == 'POST':
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             raw_password = form.cleaned_data.get('password1')
#             user = authenticate(username=username, password=raw_password)
#             login(request, user)
#             return redirect('/')
#         else: context = {'form': form}
#     return render(request, "scg_app/register.html", context)
