# -*- coding: utf-8 -*-
import datetime
import re
import math
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.shortcuts import render, redirect, reverse, get_object_or_404
from requests.exceptions import ConnectionError, HTTPError
from scg_app.forms import *
from scg_app.models import *
from zeep import Client
from django.contrib import messages
from django.apps import apps

from django.core.paginator import EmptyPage, Paginator
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import defaultdict

from dal import autocomplete
try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy
from django.forms import inlineformset_factory, model_to_dict
from django.views import generic
from django.http import JsonResponse, Http404
from django.core import serializers


@login_required
def certificados_list(request, id_clase:int, context=None):
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
    clase = get_object_or_404(Clase, pk=pk)

    if request.method == 'POST':
        form = ClaseUpdForm(request.POST, instance=clase)
        if not form.is_valid():
            messages.error(request, f'Error de formulario.')
            context = context or {'form': ClaseUpdForm(instance=clase)}
            return render(request, 'apps/scg_app/clase_edit.html', context)

        clase = form.save(commit=False)

        if clase.parent_recurrencia:
            if clase.horario_desde != clase.parent_recurrencia.horario_desde or clase.horario_hasta != clase.parent_recurrencia.horario_hasta:
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
    return render(request, "base_template.html", {})

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

class EmpleadosList(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'apps/scg_app/empleados_list.html'
    context_object_name = 'empleados_list'

    paginator_class = SafePaginator
    paginate_by = 25

    ordering = ['apellido', 'nombre',]

class SaldosList(LoginRequiredMixin, ListView):
    model = Saldo
    template_name = 'scg_app/saldos_list.html'
    context_object_name = 'saldos_list'

    paginator_class = SafePaginator
    paginate_by = 25

    ordering = ['desde', 'sede__nombre', 'actividad__nombre']

def confirm_delete(request, model, pk, context=None):

    try:
        _model = apps.get_model('scg_app', model)
    except:
        raise Http404(f'No existe el modelo {model}')

    obj = get_object_or_404(_model, pk=pk)

    context = {
        "pronoun": obj.pronombre,
        "model": re.sub(r'([A-Z])', r' \1', obj.__class__.__name__
                ).replace(' ', '', 1).capitalize(),
        "object": obj
    }

    if request.method == "POST":
        messages.success(request, f'Se ha eliminado {context["pronoun"]} {context["model"]}.')
        try:
            success_url = obj.pos_delete_url()
        except:
            success_url = 'index'
        
        obj.delete()
        return redirect(success_url)

    return render(request, "apps/scg_app/confirm_delete.html", context)


def programar(request, context=None):

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
                return render(request, "apps/scg_app/programar_clase.html", context)

        try:    #process data geted by API
            fields = {
                "empleado" : get_object_or_404(Empleado, pk=request.POST.get("empleados-results")),
                "actividad" : get_object_or_404(Actividad, pk=request.POST.get("actividades-results")),
                "sede" : get_object_or_404(Sede, pk=request.POST.get("sedes-results")),
            }
        except:
            messages.error(request, "Error en campos de búsqueda.")
            return render(request, "apps/scg_app/programar_clase.html", context)

        ###validate info and process more data
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, "apps/scg_app/programar_clase.html", context)

        fields.update({
            "dia_semana": form.cleaned_data["dia_semana"], 
            "fecha_desde": datetime.date.fromisoformat(form.cleaned_data["fecha_desde"]), 
            "fecha_hasta": datetime.date.fromisoformat(form.cleaned_data["fecha_hasta"]), 
            "horario_desde": form.cleaned_data["horario_desde"].replace(second=0, microsecond=0),  #limpiando segundos innecesarios
            "horario_hasta": form.cleaned_data["horario_hasta"].replace(second=0, microsecond=0),  #limpiando segundos innecesarios
        })

        #context["form"] = form        

        if fields["fecha_hasta"] < datetime.date.today() and not settings.DEBUG:
            messages.error(request, "No se pueden programar clases para fechas pasadas.")
            return render(request, "apps/scg_app/programar_clase.html", context)

        if fields["fecha_desde"] >= fields["fecha_hasta"]:
            messages.error(request, "La fecha de fin debe ser mayor a la de inicio.")
            return render(request, "apps/scg_app/programar_clase.html", context)

        if fields["horario_desde"] >= fields["horario_hasta"]:
            messages.error(request, "La hora de fin debe ser mayor a la de inicio.")
            return render(request, "apps/scg_app/programar_clase.html", context)

        if not Saldo.objects.filter(
            actividad=fields["actividad"], 
            sede=fields["sede"], 
            desde__lte=fields["fecha_desde"],
            hasta__gte=fields["fecha_hasta"]
        ).exists():
            messages.error(request, f'No hay saldos para la actividad en la sede seleccionada.')
            return render(request, "apps/scg_app/programar_clase.html", context)

        _to_delete = []
        for dia in fields["dia_semana"]:
            _used = Recurrencia.in_use(
                employee=fields["empleado"],
                week_day=dia,
                date_ini=fields["fecha_desde"],
                date_end=fields["fecha_hasta"],
                hour_ini=fields["horario_desde"],
                hour_end=fields["horario_hasta"])
            
            _to_delete.append(dia) if _used else None 
        
        [fields["dia_semana"].remove(dia) for dia in _to_delete]

        if not fields["dia_semana"]:
            messages.error(request, f'Todos los días estan cubiertos por otras programaciones.')
            return render(request, "apps/scg_app/programar_clase.html", context)

        _not_success, _rejecteds, _creadas = False, False, 0

        for dia in fields["dia_semana"]:
            rec = Recurrencia.objects.create(
                dia_semana=dia, 
                fecha_desde=fields["fecha_desde"], 
                fecha_hasta=fields["fecha_hasta"], 
                horario_desde=fields["horario_desde"], 
                horario_hasta=fields["horario_hasta"], 
                empleado=fields["empleado"], 
                actividad=fields["actividad"], 
            )
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
            messages.warning(request, 'No se crearon algunas clases porque el empleado no estaba disponible ciertos días y horarios.')
        
        if _to_delete:
            messages.warning(request, "No se crearon todas las programaciones por falta de disponibilidad.")
        else:
            messages.success(request, "Programación generada!")

    return render(request, "apps/scg_app/programar_clase.html", context)

def generar_clases(_fields, _dia, _recurrencia):

    #print(_dia)
    #dias = dict(settings.DIA_SEMANA_CHOICES) #get from settings
    success, rejected, cant_creadas = True, 0, 0 

    try:
        #+1 for process all days
        num_dias = (_fields["fecha_hasta"] - _fields["fecha_desde"]).days + 1

        for i in range(num_dias):
            dia_actual = _fields["fecha_desde"] + datetime.timedelta(days=i)

            #print(str(dia_actual.weekday()), str(_dia))

            if str(dia_actual.weekday()) == str(_dia):
                if not _fields["empleado"].is_busy(
                                            dia_actual, 
                                            _fields["horario_desde"], 
                                            _fields["horario_hasta"]):
                    Clase.objects.create(
                        parent_recurrencia = _recurrencia,
                        parent = _recurrencia.__str__(),
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
            for field in Empleado._meta.fields:
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
            success, error = confirmar_clases(ids)
            messages.success(request, f'Se {"confirmaron" if success > 1 else "confirmó"} {success} clase(s).') if success else None
            messages.error(request, f'No se {"pudieron" if error > 1 else "pudo"} confirmar {error} clase(s) porque esta(n) cancelada(s).') if error else None

            return redirect('clases_view')

        if _accion == 'gestion_recurrencia':
            if len(ids) != 1:
                messages.error(request, "Debe seleccionar solo una clase para gestionar su programación.")
                return redirect('clases_view')

            messages.warning(request, "Acción aún no implementada.")
            return redirect('clases_view')

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

def confirmar_clases(_ids):
    clases = Clase.objects.filter(pk__in=_ids)
    _success, _error = (0, 0)

    if not clases:
        return _success, _ids

    for clase in clases:
        #check if class is not cancelled
        if clase.is_cancelled:
            _error += 1
        else:  
            clase.confirmada = True
            clase.save()
            _success += 1

    return _success, _error

@login_required
def gestion_ausencia(request, ids_clases=None, context=None):

    #in errors only
    if not ids_clases:
        return render(request, "apps/scg_app/gestion_ausencia.html", context)

    if request.method == 'POST':
        form = MotivoAusenciaForm(request.POST, request.FILES)
    else:
        form = MotivoAusenciaForm()
    
    context = context or {'form': form}

    clases_to_edit = Clase.objects.filter(pk__in=ids_clases.split('-'))
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

    form = ReemplazoForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    if not id_clase:
        return render(request, "apps/scg_app/gestion_reemplazo.html", context)

    clase_to_edit = get_object_or_404(Clase, pk=id_clase)
    context["clase_to_edit"] = clase_to_edit

    if request.method == 'POST':
        #form = ReemplazoForm(request.POST)
        if form.is_valid():
            reemplazante = form.cleaned_data["reemplazo"]

            if not reemplazante:
                clase_to_edit.reemplazo = None
                clase_to_edit.save()
                clase_to_edit.update_status()
                messages.success(request, "Se ha borrado el reemplazo.")
                return render(request, "apps/scg_app/gestion_reemplazo.html", context)

            if clase_to_edit.empleado == reemplazante:
                messages.error(request, "El reemplazante no puede ser el empleado asignado.")
                return render(request, "apps/scg_app/gestion_reemplazo.html", context)

            if reemplazante.is_busy(fecha=clase_to_edit.fecha, inicio=clase_to_edit.horario_desde, fin=clase_to_edit.horario_hasta):
                messages.error(request, "El reemplazante no está disponible en el rango horario de esta clase.")
                return render(request, "apps/scg_app/gestion_reemplazo.html", context)

            clase_to_edit.reemplazo = reemplazante
            clase_to_edit.save()
            clase_to_edit.update_status()

            messages.success(request, "Reemplazo cargado con éxito!")

    return render(request, "apps/scg_app/gestion_reemplazo.html", context)

@login_required
def gestion_marcajes(request, id_empleado=None, fecha=None, context=None):
    #validate url format
    #print(fecha)
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
    day_classes = Clase.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('horario_desde')
    day_blocks = BloqueDePresencia.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('inicio__hora')
    #day_clockings = Marcaje.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('entrada')

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

            day_blocks = BloqueDePresencia.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('inicio')
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


### from tbs ###
@user_passes_test(check_admin)
def pulldbs(request): return render(request, "scg_app/pull_dbs.html", {})

def pulldb_generic(tabla, filtros):
    """Usa el namespace 'tabla' y la lista de filtros 'filtros' para hacer un request ListField y obtener todos los registros y los campos de los filtros"""
    contents = []
    try:
        client = Client(settings.SERVER_URL)
        ns4 = client.type_factory('ns4')
        payload = ns4.ArrayOfstring(filtros)
        db = client.service.ListFields(tabla, payload, '')
        for db_records in db["KeyValueOfstringanyType"]:
            content = []
            campos = db_records["Value"]["Data"]["KeyValueOfstringanyType"]
            [content.append([data["Value"]]) for data in campos]
            contents.append(content)

    except ConnectionError: contents = "VPN desconectada o red caida!"
    except HTTPError: contents = "404!, la url no es valida"
    return contents

@user_passes_test(check_admin)
def pull_empleados(request):
    empleados, context = Empleado.objects, {}
    emp_records_init = empleados.count()
    empleados_db = pulldb_generic("Employee", ["id", "name", "nameEmployee", "lastName", "companyCode", "employeeCode", "persoTipo", ]) #fetch empleados

    if type(empleados_db) == list:
        for empleado in empleados_db:
            user = empleados.filter(id=empleado[0][0])
            if user.exists(): user.update(dni=empleado[1][0], nombre=empleado[2][0], apellido=empleado[3][0], empresa=empleado[4][0], legajo=empleado[5][0])
            else: user = empleados.update_or_create(id=empleado[0][0], dni=empleado[1][0], nombre=empleado[2][0], apellido=empleado[3][0], empresa=empleado[4][0], legajo=empleado[5][0])
        
        if emp_records_init < Empleado.objects.count():
            messages.success(request, "Tabla de empleados importada correctamente!")
        else:
            messages.success(request, "Datos de empleados actualizados correctamente!")
    else: 
        messages.error(request, empleados_db)
        #context['status'] = empleados_db
    return render(request, "apps/scg_app/pull_empleados.html", context)

@user_passes_test(check_admin)
def pull_sedes(request):
    sedes, context = Sede.objects, {}
    sedes_records_init = sedes.count()
    sedes_db = pulldb_generic("Custom", ["id", "name", "type", ]) #fetch sedes/custom

    if type(sedes_db) == list:
        for sede in sedes_db:
            location = sedes.filter(id=sede[0][0])
            if location.exists(): location.update(nombre=sede[1][0])
            else: sedes.update_or_create(id=sede[0][0], nombre=sede[1][0])
        context['status'] = "Tabla de sedes importada correctamente!" if sedes_records_init < Sede.objects.count() else "Datos de sedes actualizados correctamente!"
    else: 
        messages.error(request, sedes_db)
        #context['status'] = sedes_db
    return render(request, "apps/scg_app/pull_sedes.html", context)

def register(request):
    form = SignUpForm()
    context = {'form': form}
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
        else: context = {'form': form}
    return render(request, "scg_app/register.html", context)

@user_passes_test(check_admin)
def pull_clockings(request):
    context, marcajes, empleados = {}, [], Empleado.objects.all()
    for empleado in empleados:
        eid, tipo = empleado.id, "Attendance" #hardcodeado, por ahora. Posibles valores: ["Attendance", "Access", "Visit"]
        fin = datetime.datetime(2020, 1, 3, 23, 59) #hardcodeado para testeo, dps va a ser --> datetime.datetime.now().date
        marcaje = get_clockings(eid, fin, tipo)
        if type(marcaje) == list: marcajes += marcaje
    context["marcajes"] = marcajes
    return render(request, "scg_app/pull_clockings.html", context)

def get_clockings(eid, fin, tipo):
    contents = []
    try:
        client = Client(settings.SERVER_URL)
        inicio = fin - datetime.timedelta(days=3)
        contents = client.service.Clockings(eid, inicio, fin, tipo)
    except ConnectionError: contents = "VPN desconectada o red caida!"
    except HTTPError: contents = "404!, la url no es valida"
    return contents

@user_passes_test(check_admin)
def auto_clockings(request):
    context, resultado = {}, compare_clockigns(True)
    if resultado[-1]: context = {"status": "Operacion finalizada exitosamente!", "resultados": resultado[0]}
    else: context["status"] = "Operacion finalizada con errores"
    return render(request, "scg_app/auto_clockings.html", context)

def compare_clockigns(update=False):
    offsets_inicio_clase, offsets_fin_clase, success, pull_data, matcheos, clockings = (15, 10), (5, 20), False, [], [], []
    clases, reemplazos, ausencias, actividades, empleados, marcajes = Clase.objects.all(), Reemplazo.objects.all(), Ausencia.objects.all(), Actividad.objects.all(), Empleado.objects.all(), Marcaje.objects.all()
    if update:
        #"""
        for empleado in empleados:
            eid, tipo, fin = empleado.id, "Attendance", datetime.datetime(2020, 1, 3, 23, 59) #hardcodeado para testeo, dps va a ser --> datetime.datetime.now().date
            marcaje = get_clockings(eid, fin, tipo)
            if type(marcaje) == list: pull_data += marcaje
        """
        pull_data = [ #faster test-data
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 6, 35),'IP': '192.168.1.182','IdClocking': 14,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 10, 0),'IP': '192.168.1.182','IdClocking': 15,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 15, 50),'IP': '192.168.1.182','IdClocking': 16,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 18, 50),'IP': '192.168.1.182','IdClocking': 17,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},

            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 5, 45),'IP': '192.168.1.182','IdClocking': 18,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 9, 5),'IP': '192.168.1.182','IdClocking': 19,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 10, 50),'IP': '192.168.1.182','IdClocking': 20,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 12, 55),'IP': '192.168.1.182','IdClocking': 21,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 17, 20),'IP': '192.168.1.182','IdClocking': 22,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 20, 55),'IP': '192.168.1.182','IdClocking': 23,'IdEmployer': 1,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},

            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 6, 15),'IP': '192.168.1.182','IdClocking': 24,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 9, 25),'IP': '192.168.1.182','IdClocking': 25,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 12, 15),'IP': '192.168.1.182','IdClocking': 26,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 15, 25),'IP': '192.168.1.182','IdClocking': 27,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 18, 10),'IP': '192.168.1.182','IdClocking': 28,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 2, 21, 5),'IP': '192.168.1.182','IdClocking': 29,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},

            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 6, 45),'IP': '192.168.1.182','IdClocking': 30,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
            {'AllDay': False,'CardNumber': None,'ClockingType': 18,'Datetime': datetime.datetime(2020, 1, 3, 15, 25),'IP': '192.168.1.182','IdClocking': 31,'IdEmployer': 2,'IdReader': -1,'IdTerminal': -1,'IdTimeType': 0,'IdZone': -1,'Source': 8,'State': 0,'User': 'Admin'},
        ]
        #"""

        fin = datetime.datetime(2020, 1, 3, 23, 59) #hardcodeado para testeo, dps va a ser --> datetime.datetime.now().date
        inicio = fin - datetime.timedelta(days=3)
        clases = clases.filter(fecha__gte=inicio.strftime("%Y-%m-%d"), fecha__lte=fin.strftime("%Y-%m-%d")).order_by('fecha', 'horario_desde') #filtro: rango de fechas

        for i in range(max([m["IdEmployer"] for m in pull_data]) + 1): #los indices claramente empiezan por 0, pero los ids en 1
            marcaje_empleado = [marcaje for marcaje in pull_data if marcaje['IdEmployer']==i]
            if marcaje_empleado:
                j = 0
                while j < len(marcaje_empleado):
                    clocking_tmp = Marcaje(
                        id=None,
                        empleado=empleados.filter(id=i)[0],
                        fecha=marcaje_empleado[j]["Datetime"].date(),
                        entrada=marcaje_empleado[j]["Datetime"].time(),
                        salida=marcaje_empleado[j + 1]["Datetime"].time() if j + 1 < len(marcaje_empleado) else None
                    )
                    j += 2
                    if not(marcajes.filter(empleado=clocking_tmp.empleado, fecha=clocking_tmp.fecha, entrada=clocking_tmp.entrada, salida=clocking_tmp.salida).exists()): clockings.append(clocking_tmp)
                    #if check_marcaje_unique(marcajes, clocking_tmp): clockings.append(clocking_tmp)
        marcajes.bulk_create(clockings)

    for marcaje in marcajes:
        sub_clases = clases.filter(fecha=marcaje.fecha, empleado=marcaje.empleado, horario_desde__gte=marcaje.entrada, horario_hasta__lte=marcaje.salida) if marcaje.salida else clases.filter(fecha=marcaje.fecha, empleado=marcaje.empleado, horario_hasta__lte=marcaje.entrada)
        for clase in sub_clases:
            clase.presencia = settings.PRESENCIA_CHOICES[-1][-1]
            clase.save()
            success = True
            matcheos.append([clase, True])
    return matcheos, success

def time_ops(f1, f2, sum=None): #para usar los offsets --> offsets_inicio_clase, offsets_fin_clase = (15, 10), (5, 20)
    date1 = datetime.datetime.now().replace(hour=f1.hour, minute=f1.minute, second=0, microsecond=0)
    date2 = datetime.timedelta(hours=f2.hour, minutes=f2.minute, seconds=0, microseconds=0)
    return (date1 - date2) if not sum else (date1 + date2)

def historizar():
    #todo
    return
