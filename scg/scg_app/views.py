# -*- coding: utf-8 -*-

### built-in ###
from collections import defaultdict
import datetime
import re
import math

### third ###
#...

### django ###
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, \
    permission_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from requests.exceptions import ConnectionError, HTTPError
from django.core.paginator import EmptyPage, Paginator
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.apps import apps
from django.http import HttpResponseRedirect

### own ###
from django.conf import settings
from scg_app.forms import *
from scg_app.models import *
import scg_app.tasks as task_mgmt

def check_admin(user):
    return user.is_superuser

@login_required
def comments_of_class(request, id_clase: int, context=None):
    """ Lists all comments of a specific class. """

    template = "apps/scg_app/clase/comentarios.html"
    clase = get_object_or_404(Clase, pk=id_clase)

    #check sede permission
    if not request.user.has_sede_permission(clase.sede):
        messages.error(
            request, "No tiene permisos para la sede de esta clase.")
        return render(request, template, context)

    #if clase is locked, doesn't support actions
    if request.method == "POST" and not clase.locked:

        if 'add_comment' in request.POST:
            form = ComentarioForm(request.POST)

            if not form.is_valid():
                messages.error(request, 'Error de formulario.')
                return render(request, template, context)

            #create comment
            new_comment = Comentario.objects.create(
                usuario=request.user,
                accion=settings.ACCIONES_CHOICES[-1][0],
                contenido=form.cleaned_data["comentario"])

            #assign comment to
            clase.comentarios.create(comentario=new_comment)
            clase.save()
        
        if 'update_comment' in request.POST:
            upd_comm = get_object_or_404(
                Comentario, pk=request.POST.get('comment_id'))

            if request.user == upd_comm.usuario or request.user.is_superuser:
                form_update = ComentarioForm(request.POST)

                if not form_update.is_valid():
                    messages.error(request, 'Error de formulario.')
                    return render(request, template, context)
                
                #update comment
                upd_comm.contenido = form_update.cleaned_data["comentario"]
                upd_comm.fecha = datetime.date.today()
                upd_comm.hora = datetime.datetime.now().time()
                upd_comm.save()
            else:
                messages.error(request, "No puede editar este comentario")

    #reset form
    form = ComentarioForm()

    #after permissions checks
    comments = [comment.comentario for comment in clase.comentarios.all()]

    context = {
        "clase": clase,
        "comentarios": comments,
        "form": form,
    }

    return render(request, template, context)

@login_required
def certificados_list(request, id_clase: int, context=None):
    """ Lists all the justifications for which files were
        attached with their corresponding reasons.
    """

    template = "apps/scg_app/certificados.html"
    clase = get_object_or_404(Clase, pk=id_clase)

    #check sede permission
    if not request.user.has_sede_permission(clase.sede):
        messages.error(
            request, "No tiene permisos para la sede de esta clase.")
        return render(request, template, context)

    #after permission checks
    certificados = Certificado.objects.filter(clases__in=[clase])

    _ids = set()
    for certificado in certificados:
        for clase in certificado.clases.all():
            _ids.add(clase.id)

    clases_impacto = Clase.objects.filter(id__in=_ids)

    context = {
        "certificados": certificados,
        "clase": clase,
        "clases_impacto": clases_impacto,
    }

    return render(request, template, context)

@login_required
def clase_edit(request, pk, context=None):
    """ It lists all the justifications for which files were attached with \
        their corresponding reasons.
        Does not allow overlap with a different class.
    """

    template = 'apps/scg_app/clase_edit.html'
    clase = get_object_or_404(Clase, pk=pk)
    form = ClaseUpdForm(instance=clase)
    
    context = context or {'form': form, 'comment_form': ComentarioForm()}

    #check edit permission
    if clase.locked or not request.user.has_perm('scg_app.change_clase'):
        context["locked"] = True

        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> esta bloqueado o no \
            tiene permiso para editar clases.'.format(
                Periodo.get_url_date_period(clase.fecha)
            ))
        return render(request, template, context)

    #check sede permission
    if not request.user.has_sede_permission(clase.sede):
        messages.error(request, "No tiene permisos para la sede de esta clase.")
        context["locked"] = True
        return render(request, template, context)

    if request.method == 'POST':
        form = ClaseUpdForm(request.POST, instance=clase)
        comment_form = ComentarioForm(request.POST)

        if not form.is_valid() or not comment_form.is_valid():
            messages.error(request, 'Error de formulario.')
            context = context or {'form': ClaseUpdForm(instance=clase)}
            return render(request, template, context)

        clase = form.save(commit=False)

        if clase.recurrencia:
            if (clase.horario_desde != clase.recurrencia.horario_desde or
                clase.horario_hasta != clase.recurrencia.horario_hasta):

                if Empleado.is_busy(
                        clase.empleado, clase.fecha, 
                        clase.horario_desde, clase.horario_hasta,
                        rec_ignore=clase.recurrencia):

                    messages.error(
                        request, "La edición se superpone con otra clase.")
                    return render(request, template, context)

                clase.modificada = True
                messages.success(
                    request,
                    f'La clase ha sido modificada como excepción a la serie.')
            else:
                clase.modificada = False
                messages.success(request, f'La clase ha sido modificada.')

        #create comment
        if comment_form.cleaned_data["comentario"]:
            new_comment = Comentario.objects.create(
                usuario=request.user,
                accion='edicion',
                contenido=comment_form.cleaned_data["comentario"])

            #assign comment to
            clase.comentarios.create(comentario=new_comment)

        clase.save()

        context['form'] = form
        return render(request, template, context)

    form = ClaseUpdForm(instance=clase)
    context = context or {'form': form}

    return render(request, template, context)

@login_required
def index(request):
    return render(request, "index.html", {})

def about(request):
    return render(request, "scg_app/about.html", {})

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

    if not request.user.has_perm('scg_app.add_periodo'):
        context["locked"] = True
        messages.error(request, 'No tiene permisos para crear periodos')
        return render(request, "apps/scg_app/create/periodo.html", context)

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
            request,
            '<a href="{}" class="no-recore">Periodo</a> creado.'.format(
                new_period.get_edit_url()))
        return redirect('periodos_view')


    return render(request, "apps/scg_app/create/periodo.html", context)


@login_required
def periodo_update(request, pk, context=None):
    """ Allows updating the data of a Periodo.
        It does not allow the overlap with another already generated.
    """
    periodo = get_object_or_404(Periodo, pk=pk)

    #check edit permission
    if not request.user.has_perm('scg_app.change_periodo'):
        messages.error(request, 'No tiene permiso para editar periodos.')
        form = PeriodoUpdForm(instance=periodo)
        context = {'form': form}
        context["locked"] = True

        return render(request, 'apps/scg_app/create/periodo.html', context)

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
                id_exclude=periodo.pk):
            messages.error(request,
                           "El periodo se superpone con otro ya creado.")
            return render(request, "apps/scg_app/create/periodo.html", context)

        #after of all checks
        periodo.save()

        #lock or allor related objects
        affecteds = periodo.update_related()

        messages.success(
            request,
            '<a href="{}" class="no-decore">Periodo</a> actualizado.'.format(
                periodo.get_edit_url()))
        return redirect('periodos_view')

    form = PeriodoUpdForm(instance=periodo)
    context = {'form': form}

    return render(request, 'apps/scg_app/create/periodo.html', context)

@login_required
def confirm_delete(request, model, pk, context=None):
    """ view to confirm delete an object from a specific model """

    try:
        _model = apps.get_model('scg_app', model)
    except LookupError:
        _model = apps.get_model('help', model)
    except:
        raise Http404(f'No existe el modelo {model}')
    
    obj = get_object_or_404(_model, pk=pk)

    context = {
        "pronoun": obj.pronombre,
        #convert "ModelName" to "Model name"
        "model": re.sub(
            r'([A-Z])', 
            r' \1', obj.__class__._meta.verbose_name
            ).replace(' ', '', 1).capitalize(),
        "object": obj,
        "locked": False
    }

    #check delete permission
    if not request.user.has_perm(f'scg_app.delete_{model.lower()}'):
        context["locked"] = True
        messages.error(request, 'No tiene permisos para eliminar este objeto.')
        return render(request, "apps/scg_app/confirm_delete.html", context)

    #check locked and bloqueado properties
    if getattr(obj, 'locked', False) or getattr(obj, 'bloqueado', False):
        context["locked"] = True
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

    template = 'apps/scg_app/create/saldo.html'

    saldo = get_object_or_404(Saldo, pk=pk)
    form = SaldoUpdForm(instance=saldo)
    context = {'form': form}
    
    #check change permission
    if not request.user.has_perm('scg_app.change_saldo'):
        messages.error(request, 'No tiene permiso para editar saldos.')
        context["locked"] = True
        return render(request, template, context)

    #check sede permission
    if not request.user.has_sede_permission(saldo.sede):
        messages.error(request, "No tiene permisos para esta sede.")
        context["locked"] = True
        return render(request, template, context)

    if request.method == 'POST':
        form = SaldoUpdForm(request.POST, instance=saldo)
        context = context or {'form': SaldoUpdForm(instance=saldo)}

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, template, context)

        saldo = form.save(commit=False)

        if Saldo.check_overlap(
                _sede=saldo.sede,
                _actividad=saldo.actividad,
                _desde=saldo.desde,
                _hasta=saldo.hasta,
                id_exclude=saldo.pk):
            messages.error(request,
                "El periodo se superpone con otro ya creado.")
            return render(request, template, context)

        #after of all checks
        saldo.save()

        messages.success(
            request,
            '<a href="{}" class="no-decore">Saldo</a> actualizado.'.format(
                saldo.get_edit_url()))
        return redirect('saldos_view')

    form = SaldoUpdForm(instance=saldo)
    context = {'form': form}

    return render(request, template, context)

@login_required
def generar_saldo(request, context=None):
    """ Allows create a Saldo.
        It does not allow the overlap with another already generated.
    """

    template = "apps/scg_app/create/saldo.html"

    form = SaldoForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    #check add permission
    if not request.user.has_perm('scg_app.add_saldo'):
        context["locked"] = True
        messages.error(request, 'No tiene permisos para crear saldos')
        return render(request, template, context)

    if request.method == 'POST':
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, template, context)

        #check sede permission
        if not request.user.has_sede_permission(form.cleaned_data.get("sede")):
            messages.error(request, "No tiene permisos para esta sede.")
            return render(request, template, context)

        if Saldo.check_overlap(
                _sede=form.cleaned_data.get("sede"),
                _actividad=form.cleaned_data.get("actividad"),
                _desde=form.cleaned_data.get("desde"),
                _hasta=form.cleaned_data.get("hasta")):
            messages.error(request,
                "El periodo se superpone con otro ya creado.")
            return render(request, template, context)

        #after of security checks
        new_saldo = Saldo.objects.create(
            sede = form.cleaned_data.get("sede"),
            actividad = form.cleaned_data.get("actividad"),
            desde = form.cleaned_data.get("desde"),
            hasta = form.cleaned_data.get("hasta"), 
            saldo_asignado = form.cleaned_data.get("saldo_asignado"), 
        )

        messages.success(
            request,
            '<a href="{}" class="no-decore">Saldo</a> generado.'.format(
                new_saldo.get_edit_url()))
        return redirect('saldos_view')

    return render(request, template, context)

@login_required
def programar(request, context=None):
    """ create a Recurrencia and classes with corresponding data """

    template = "apps/scg_app/create/programacion.html"
    form = RecurrenciaForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form, 'search_data': {}}

    if not request.user.has_perm('scg_app.add_recurrencia'):
        context["locked"] = True
        messages.error(request, 'No tiene permisos para crear programaciones')
        return render(request, template, context)

    if request.method == 'POST':

        search_data = {
            "empleado": request.POST.get('empleados-search'),
            "actividad": request.POST.get('actividades-search'),
            "sede": request.POST.get('sedes-search'),
        }
        context["search_data"] = search_data

        if ("empleados-results" and "actividades-results" and 
                "sedes-results" not in request.POST.keys()):
            messages.warning(
                request, "Busque y seleccione los datos en desplegables.")
            return render(request, template, context)

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
            return render(request, template, context)

        ###validate info and process more data
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, template, context)

        #check sede permission
        if not request.user.has_sede_permission(fields.get('sede')):
            messages.error(
                request, "No tiene permisos para la sede seleccionada.")
            return render(request, template, context)

        fields.update({
            #"dia_semana": form.cleaned_data["dia_semana"],
            "weekdays": form.cleaned_data["weekdays"],
            "fecha_desde": datetime.date.fromisoformat(
                form.cleaned_data["fecha_desde"]),
            "fecha_hasta": datetime.date.fromisoformat(
                form.cleaned_data["fecha_hasta"]),
            "horario_desde": form.cleaned_data["horario_desde"].replace(
                second=0, microsecond=0),
            "horario_hasta": form.cleaned_data["horario_hasta"].replace(
                second=0, microsecond=0),
        })

        ### dates validate
        if fields["fecha_hasta"] < datetime.date.today() and not settings.DEBUG:
            messages.error(
                request, "No se pueden programar clases para fechas pasadas.")
            return render(request, template, context)

        if fields["fecha_desde"] >= fields["fecha_hasta"]:
            messages.error(
                request, "La fecha de fin debe ser mayor a la de inicio.")
            return render(request, template, context)

        if fields["horario_desde"] >= fields["horario_hasta"]:
            messages.error(
                request, "La hora de fin debe ser mayor a la de inicio.")
            return render(request, template, context)

        if not settings.DEBUG:
            if not Saldo.objects.filter(
                    actividad=fields["actividad"],
                    sede=fields["sede"],
                    desde__lte=fields["fecha_desde"],
                    hasta__gte=fields["fecha_hasta"]).exists():
                messages.error(
                    request,
                    f'No hay saldos para la actividad en la sede seleccionada.')
                return render(request, template, context)

        #check if overlaps with another exist rec
        overlays = Recurrencia.check_overlap(
            employee=fields["empleado"],
            weekdays=fields["weekdays"],
            desde=fields["fecha_desde"],
            hasta=fields["fecha_hasta"],
            hora_ini=fields["horario_desde"],
            hora_end=fields["horario_hasta"]
        )
        if overlays:
            messages.error(
                request,
                f'La programación se superpone con {overlays} ya creada/s.')
            return render(request, template, context)

        ### check if period is locked
        period_locked = Periodo.check_overlap(
            _desde=fields.get("fecha_desde"),
            _hasta=fields.get("fecha_hasta"),
            locked_only=True
        )
        if period_locked:
            messages.error(
                request, f'La programación se solapa con un periodo bloqueado.')
            return render(
                request, template, context)

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
                fields["fecha_desde"], fields["fecha_hasta"]):
            messages.warning(
                request, 'Ya no dispone de saldo en periodos puntuales.')

        if _not_success:
            messages.warning(
                request,
                'Programación creada pero no se crearon clases puntuales.')
        elif _rejecteds:
            messages.warning(
                request, 
                'No se crearon algunas clases porque el empleado no estaba \
                disponible ciertos días y horarios.'.replace('\t', '')
            )

        #generated
        messages.success(
            request,
            '<a href="{}" class="no-decore">Programación</a> generada.'.format(
                rec.get_edit_url()))
        return redirect('programaciones_view')

    return render(request, template, context)

@login_required
def programacion_update(request, pk, context=None):
    """ update a Recurrencia and classes with corresponding data """

    template = "apps/scg_app/update/programacion.html"

    old_rec = get_object_or_404(Recurrencia, pk=pk)
    rec = get_object_or_404(Recurrencia, pk=pk)

    form = RecurrenciaUpdForm(instance=rec)
    context = {
        "form": form,
        "empleado": rec.empleado,
        "actividad": rec.actividad,
        "sede": rec.sede,
    }

    #check change permission
    if not request.user.has_perm('scg_app.change_recurrencia'):
        messages.error(request, 'No tiene permiso para editar programaciones.')
        context["locked"] = True
        return render(request, template, context)

    #check sede permission
    if not request.user.has_sede_permission(rec.sede):
        messages.error(request, "No tiene permisos para esta sede.")
        context["locked"] = True
        return render(request, template, context)

    if request.method == 'POST':
        form = RecurrenciaUpdForm(request.POST, instance=rec)
        context["form"] = form

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, template, context)

        ### dates and times validate
        fields = {
            "fecha_desde": datetime.date.fromisoformat(
                form.cleaned_data.get("fecha_desde")),
            "fecha_hasta": datetime.date.fromisoformat(
                form.cleaned_data.get("fecha_hasta")),
            "horario_desde": form.cleaned_data.get(
                "horario_desde").replace(second=0, microsecond=0),
            "horario_hasta": form.cleaned_data.get(
                "horario_hasta").replace(second=0, microsecond=0),
            "weekdays": form.cleaned_data.get("weekdays"),
            "empleado": rec.empleado,
            "actividad": rec.actividad,
            "sede": rec.sede,
        }

        if fields.get("fecha_hasta") < datetime.date.today() and not settings.DEBUG:
            messages.error(
                request, "No se pueden programar clases para fechas pasadas.")
            return render(request, template, context)

        if fields.get("fecha_desde") >= fields.get("fecha_hasta"):
            messages.error(
                request, "La fecha de fin debe ser mayor a la de inicio.")
            return render(request, template, context)

        if fields.get("horario_desde") >= fields.get("horario_hasta"):
            messages.error(
                request, "La hora de fin debe ser mayor a la de inicio.")
            return render(request, template, context)

        if fields.get("fecha_desde") < old_rec.fecha_desde:
            messages.error(
                request, "No se puede extender una programación hacia atrás.")
            return render(request, template, context)

        overlays = Recurrencia.check_overlap(
            employee=rec.empleado,
            weekdays=form.cleaned_data.get("weekdays"),
            desde=form.cleaned_data.get("fecha_desde"),
            hasta=form.cleaned_data.get("fecha_hasta"),
            hora_ini=form.cleaned_data.get("horario_desde"),
            hora_end=form.cleaned_data.get("horario_hasta"),
            ignore=rec.id,
        )

        if overlays:
            messages.error(
                request,
                f'La programación se superpone con {overlays} ya creada/s.')
            return render(request, template, context)

        ### dates actions ###
        if fields.get("fecha_hasta") < old_rec.fecha_hasta: #delete end differences
            classes_to_delete = Clase.objects.filter(
                recurrencia=old_rec, 
                fecha__gt=fields.get("fecha_hasta"))

            #prevent blocked delete
            if classes_to_delete.filter(locked=True):
                messages.error(
                    request, "No se pueden eliminar clases bloqueadas.")
                return render(request, template, context)
            
            #delete after of checks
            classes_to_delete.delete()

        if fields.get("fecha_desde") > old_rec.fecha_desde: #delete coming differences
            classes_to_delete = Clase.objects.filter(
                recurrencia=old_rec,
                fecha__lt=fields.get("fecha_desde"))
            
            #prevent blocked delete
            if classes_to_delete.filter(locked=True):
                messages.error(
                    request, "No se pueden eliminar clases bloqueadas.")
                return render(request, template, context)
            
            #delete after of checks
            classes_to_delete.delete()

        ### weekdays actions ###
        if fields.get("weekdays") != old_rec.weekdays:
            to_delete = set(old_rec.weekdays) - set(fields.get("weekdays"))
            Clase.objects.filter(
                recurrencia=old_rec, dia_semana__in=list(to_delete)
            ).delete()

        ### time actions ###
        exis_overlaps_classes = False
        if (fields.get("horario_desde") != old_rec.horario_desde or
                fields.get("horario_hasta") != old_rec.horario_hasta):

            clases_to_edit = Clase.objects.filter(recurrencia=old_rec)

            if clases_to_edit.filter(locked=True):
                messages.error(
                    request, "No se pueden editar clases bloqueadas.")
                return render(request, template, context)
            
            for clase in clases_to_edit:
                if not clase.empleado.is_busy(
                        clase.fecha, clase.horario_desde,
                        clase.horario_hasta, rec_ignore=rec):
                    clase.horario_desde = fields.get("horario_desde")
                    clase.horario_hasta = fields.get("horario_hasta")
                    clase.save()
                else:
                    exis_overlaps_classes = True

        #if employee is busy in specific days or times
        if exis_overlaps_classes:
            messages.warning(
                request,
                "No se pudo editar una o más clases por falta de disponibilidad"
            )

        ### create differences ###
        _not_success, _rejecteds, _creadas = False, False, 0
        for dia in fields["weekdays"]:
            success, rejected, cant_creadas = generar_clases(
                fields, dia, rec, editing=True)

            #update status vars
            _not_success = True if not success else _not_success
            _rejecteds = True if rejected != 0 else _rejecteds

        #checks saldos
        if not Saldo.check_saldos(
                fields["sede"], fields["actividad"],
                fields["fecha_desde"], fields["fecha_hasta"]):
            messages.warning(
                request, 'Ya no dispone de saldo en periodos puntuales.')

        ### Recurrencia update ###
        ### after of all security checks
        rec.weekdays = fields.get("weekdays")
        rec.fecha_desde = fields.get("fecha_desde")
        rec.fecha_hasta = fields.get("fecha_hasta")
        rec.horario_desde = fields.get("horario_desde")
        rec.horario_hasta = fields.get("horario_hasta")
        rec.save()

        #after of all checks
        messages.success(
            request,
            '<a href="{}" class="{}">Programación</a> actualizada.'.format(
                rec.get_edit_url(), "no-decore"))
        return redirect('programaciones_view')

    return render(request, template, context)

def generar_clases(_fields, _dia, _recurrencia, editing=None):
    """ create, if possible, all classes in the indicated period """

    success, rejected, cant_creadas = True, 0, 0 

    try:
        #+1 for process all days
        num_dias = (_fields["fecha_hasta"] - _fields["fecha_desde"]).days + 1

        for i in range(num_dias):
            dia_actual = _fields["fecha_desde"] + datetime.timedelta(days=i)

            if str(dia_actual.weekday()) == str(_dia):

                if Periodo.blocked_day(dia_actual):
                    rejected += 1

                elif not _fields["empleado"].is_busy(
                        dia_actual,
                        _fields["horario_desde"],
                        _fields["horario_hasta"],
                        rec_ignore=_recurrencia if editing else None
                        ):

                    Clase.objects.create(
                        recurrencia = _recurrencia,
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
    results_pp = 10 #results per page

    def post(self, request, *args, **kwargs):
        """ return json format for ajax request """

        self.results_pp = int(request.POST.get('rpp')) or self.results_pp

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

        ### tri-state checks ###
        f_ausencia = form.cleaned_data.get('solo_ausencia')
        f_ausencia = bool(f_ausencia > 0) if f_ausencia else f_ausencia
        f_reemplazos = form.cleaned_data.get('solo_reemplazos')
        f_reemplazos = bool(f_reemplazos > 0) if f_reemplazos else f_reemplazos
        f_confirm = form.cleaned_data.get('solo_confirmadas')
        f_confirm = bool(f_confirm > 0) if f_confirm else f_confirm
        f_bloqueadas = form.cleaned_data.get('solo_bloqueadas')
        f_bloqueadas = bool(f_bloqueadas > 0) if f_bloqueadas else f_bloqueadas
        
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
        if f_ausencia is not None:
            querys["f_ausencia"] = Q(ausencia__isnull=not f_ausencia)
        if f_reemplazos is not None:
            querys["f_reemplazos"] = Q(reemplazo__isnull=not f_reemplazos)
        if f_confirm is not None:
            querys["f_confirm"] = Q(confirmada=f_confirm)
        if f_bloqueadas is not None:
            querys["f_bloqueadas"] = Q(locked=f_bloqueadas)


        #get ordering data
        order_by = request.POST.get('order_by', None)
        order_by = [
            _order.replace("order_", "", 1) for _order in order_by.split(",")
        ] if order_by else None
        order_by = order_by if order_by else ('fecha',)

        #add all the filters with and critery
        query = Q()
        [query.add(v, Q.AND) for k, v in querys.items()]
        
        #filter user sede permission
        sf = Sede.objects.all()
        if not request.user.is_superuser:
            sf = request.user.sedes.all()

        #filtering with sede permission
        qs = Clase.objects.filter(sede__in=sf).filter(query).order_by(*order_by)

        total_regs = qs.count()

        #get page data
        try:
            page = int(request.POST.get('page'))
        except:
            page = 1

        reg_ini = (page - 1) * self.results_pp
        reg_end = page * self.results_pp

        #security validate
        reg_ini = 0 if reg_ini > total_regs else reg_ini
        reg_end = total_regs if reg_end > total_regs else reg_end

        #return corresponding page
        qs = qs[reg_ini:reg_end]

        #list of dict for JsonResponse
        #results = [clase.to_dict() for clase in qs]
        num_pages = math.ceil(total_regs/self.results_pp)

        return JsonResponse({
            "results": [clase.to_monitor() for clase in qs],
            "pages": num_pages,
            "page": page,
            "next": page + 1 if page < num_pages else None,
            "prev": page - 1 if page > 1 and num_pages > 1 else None,
        })

    def get_queryset(self):
        qs = Clase.objects.filter(
            fecha__gte=datetime.date.today()).order_by('fecha')
        return qs

    def get_context_data(self, *args, **kwargs):     
        context = super().get_context_data(*args, **kwargs)
        context["form"] = context.get("form") or FiltroForm(
            self.request.POST if self.request.method == 'POST' else None)
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
            messages.error(
                request,
                "Seleccione uno o más registros para ejecutar una acción.")
            return redirect('show_message', _type='error')

        ### actions ###
        if _accion == 'ver_certificados':
            if len(ids) != 1: 
                messages.error(
                    request, "Debe seleccionar solo un registro para editarlo.")
                return redirect('show_message', _type='error')
            return redirect('certificados_list', id_clase=ids[0])

        if _accion == 'editar_clases':
            if len(ids) != 1:
                messages.error(
                    request, "Debe seleccionar solo un registro para editarlo.")
                return redirect('show_message', _type='error')
            return redirect('clase_update', pk=ids[0])

        if _accion == 'gestion_ausencia':
            request.session['ids_clases'] = ids
            return redirect('gestion_ausencia')#, ids_clases='-'.join(ids))

        if _accion == 'asignar_reemplazo':
            if len(ids) != 1:
                messages.error(
                    request,
                    "Seleccione solo un registro para asignar un reemplazo.")
                return redirect('show_message', _type='error')
            return redirect('asignar_reemplazo', id_clase=ids[0])

        if _accion == 'confirmar_clases':
            request.session['ids_clases'] = ids
            return redirect('confirmar_clases')

        if _accion == 'gestion_recurrencia':
            if len(ids) != 1:
                messages.error(
                    request,
                    "Seleccione solo una clase para gestionar su programación.")
                return redirect('show_message', _type='error')

            # get the class if all verifications were correct
            clase = get_object_or_404(Clase, pk=ids[0])

            return redirect('programacion_update', pk=clase.recurrencia.id)

        if _accion == 'gestion_marcajes':
            if len(ids) != 1:
                messages.error(
                    request,
                    "Seleccione solo una clase para ver los marcajes del día.")
                return redirect('show_message', _type='error')

            # get the class if all verifications were correct
            clase = get_object_or_404(Clase, pk=ids[0])
            return redirect(
                'gestion_marcajes',
                id_empleado=clase.empleado.id,
                fecha=clase.fecha
            )
        
        if _accion == 'ver_comentarios':
            if len(ids) != 1:
                messages.error(
                    request,
                    "Seleccione solo un registro para ver los comentarios.")
                return redirect('show_message', _type='error')
            return redirect('comments_of_class', id_clase=ids[0])

    # if accessed by url or method is not POST
    messages.error(request, "Acción o método no soportado.")
    return redirect('show_message', _type='error')

@login_required
def show_message(request, _type="error", context=None):
    """ show message with a specific template for don't lost page content """

    templates = {
        "error": 'messages/error.html',
    }

    return render(request, templates.get(_type), context)

@login_required
def confirmar_clases(request, context=None):
    """ confirm all classes from the ids list """

    template = "apps/scg_app/clases_confirm.html"

    ids_clases = request.session.get('ids_clases')
    deleted = request.session.pop('ids_clases', None)

    if not ids_clases:
        messages.error(request, "No se ha seleccionado ninguna clase.")
        return render(request, template, context)

    clases = Clase.objects.filter(pk__in=ids_clases)
    
    #check confirm permission
    if not request.user.has_perm('scg_app.confirm_classes'):
        messages.error(request, "No tiene permiso para confirmar clases.")
        context = {
            "classes_error": clases,
        }
        return render(request, template, context)

    _success, _error = ([], [])
    for clase in clases:
        #check if class is not cancelled
        if (clase.is_cancelled or clase.locked or
                not request.user.has_sede_permission(clase.sede)):
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
            'No se {} confirmar {} {} porque {} {}, {} o no tiene permisos \
            sobre su sede'.format(
                "pudieron" if len(_error) > 1 else "pudo",
                len(_error),
                "clases" if len(_error) > 1 else "clase",
                "estan" if len(_error) > 1 else "esta",
                "bloqueadas" if len(_error) > 1 else "bloqueada",
                "canceladas" if len(_error) > 1 else "cancelada",
            )
        )

    context = {
        "classes_success": _success,
        "classes_error": _error,
    }
    return render(request, template, context)

@login_required
def gestion_ausencia(request, context=None):
    """
        Permite asignar un motivo, adjunto y un comentario para una clase.
        Si éste recibe un adjunto, crea un Certificado con el archivo y motivo \
        seleccionado.
    """

    template = "apps/scg_app/gestion_ausencia.html"

    ids_clases = request.session.get('ids_clases')

    #with errors only
    if not ids_clases:
        messages.error(request, "No se ha seleccionado ninguna clase.")
        return render(request, template, context)

    #print(ids)

    #form context
    if request.method == 'POST':
        form = MotivoAusenciaForm(request.POST, request.FILES)
    else:
        form = MotivoAusenciaForm()

    context = context or {'form': form}

    #check absence manage permission
    if not request.user.has_perm('scg_app.absence_management'):
        context["locked"] = True
        messages.error(request, "No tiene permiso para gestionar ausencias")
        return render(request, template, context)

    clases_to_edit = Clase.objects.filter(pk__in=ids_clases)

    #lockeds an unavailable sedes ignore
    lockeds = clases_to_edit.filter(
        Q(locked=True) | ~Q(sede__in=request.user.sedes_available()))
    lockeds_count = lockeds.count() if lockeds else 0

    if lockeds:
        messages.warning(
            request,
            "No tiene permiso para la sede de {} {} o {} {} y {} {}.".format(
                lockeds_count,
                "clases" if lockeds_count > 1 else "clase",
                "estan" if lockeds_count > 1 else "esta",
                "bloqueadas" if lockeds_count > 1 else "bloqueada",
                "fueron" if lockeds_count > 1 else "fue",
                "ignoradas" if lockeds_count > 1 else "ignorada",
            )
        )
        #put ignore in context
        context["clases_ignoradas"] = lockeds

        #exclude lockeds and unavailable sedes
        clases_to_edit = clases_to_edit.exclude(
            Q(locked=True) | ~Q(sede__in=request.user.sedes_available()))

    #if not exists classes to apply
    if not clases_to_edit:
        context["locked"] = True
        return render(request, template, context)

    context["clases_to_edit"] = clases_to_edit

    if request.method == 'POST':
        request.session['ids_clases'] = ids_clases
        
        #check valid form
        if not form.is_valid():
            messages.error(request, "Error de formulario.")
            return render(request, template, context)

        ausencia = form.cleaned_data["motivo"]
        adjunto = form.cleaned_data["adjunto"]

        #if a file was added
        if adjunto:
            certif = Certificado.objects.create(file=adjunto, motivo=ausencia)
            certif.clases.set(clases_to_edit)
        elif ausencia.requiere_certificado:
            messages.error(request, "La ausencia requiere un certificado.")
            return render(request, template, context)

        #create comment
        new_comment = None
        if form.cleaned_data["comentario"]:
            new_comment = Comentario.objects.create(
                usuario=request.user,
                accion="gestion_ausencia",
                contenido=form.cleaned_data["comentario"])

        #assign absence for each class
        for clase in clases_to_edit:
            clase.ausencia = ausencia
            #only if was added comment
            if new_comment:
                clase.comentarios.create(comentario=new_comment)
            clase.save()
            clase.update_status()

        messages.success(request, "Acción finalizada.")
        return render(request, template, context)

    #clean session data
    #deleted = request.session.pop('ids_clases', None)
    return render(request, template, context)

@login_required
def asignar_reemplazo(request, id_clase=None, context=None):
    """ Allows assign and delete a replacement to a class. """

    template = "apps/scg_app/gestion_reemplazo.html"

    if not id_clase:
        return render(request, template, context)

    clase_to_edit = get_object_or_404(Clase, pk=id_clase)

    context = context or {
        'search_data': {},
        'clase_to_edit': clase_to_edit,
        'form': ComentarioForm(),
    }

    #context["clase_to_edit"] = clase_to_edit

    #check absence manage permission
    if not request.user.has_perm('scg_app.asign_replacement'):
        context["locked"] = True
        messages.error(request, "No tiene permiso para gestionar reemplazos")
        return render(request, template, context)

    #check sede permission
    if not request.user.has_sede_permission(clase_to_edit.sede):
        context["locked"] = True
        messages.error(request, "No tiene permiso sobre esta sede")
        return render(request, template, context)

    if clase_to_edit.locked:
        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> esta bloqueado y la \
            clase no puede ser editada.'.format(
                Periodo.get_url_date_period(clase_to_edit.fecha)
            ))
        return render(request, template, context)

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
                return render(request, template, context)
        else:
            reemplazante = None

        #check comment form
        form = ComentarioForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Error en el comentario.")
            return render(request, template, context)

        if not reemplazante:
            clase_to_edit.reemplazo = None
            clase_to_edit.save()
            clase_to_edit.update_status()
            messages.success(request, "Se ha borrado el reemplazo.")
            return render(request, template, context)

        if clase_to_edit.empleado == reemplazante:
            messages.error(
                request, "El reemplazante no puede ser el empleado asignado.")
            return render(request, template, context)

        if reemplazante.is_busy(
                fecha=clase_to_edit.fecha,
                inicio=clase_to_edit.horario_desde,
                fin=clase_to_edit.horario_hasta):
            messages.error(
                request,
                "El reemplazante no está disponible en este rango horario")
            return render(request, template, context)
        
        #create comment
        new_comment = None
        if form.cleaned_data["comentario"]:
            new_comment = Comentario.objects.create(
                usuario=request.user,
                accion='gestion_reemplazo',
                contenido=form.cleaned_data["comentario"])

        #assign comment to class
        if new_comment:
            clase_to_edit.comentarios.create(comentario=new_comment)

        #replace assign
        clase_to_edit.reemplazo = reemplazante
        clase_to_edit.save()
        clase_to_edit.update_status()

        messages.success(request, "Reemplazo cargado con éxito!")

    return render(request, template, context)

@login_required
def gestion_marcajes(request, id_empleado=None, fecha=None, context=None):
    """ It shows the classes of the day of an employee and allows adding and \ 
        removing markings.
        It is also possible to recalculate the managed day. """

    template = "apps/scg_app/gestion_marcajes.html"

    form = MarcajeForm(request.POST if request.method == "POST" else None)
    context = context or {'form': form}

    try:
        id_empleado = int(id_empleado)
        fecha = datetime.date.fromisoformat(fecha)
    except:
        messages.error(request, "Error en parámetros recibidos")
        return render(request, template, context)

    empleado = Empleado.objects.filter(pk=id_empleado)
    if not empleado:
        messages.error(request, "El empleado no existe")
        return render(request, template, context)

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

    if Periodo.blocked_day(fecha):        
        context["day_locked"] = True
        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> esta bloqueado y el \
            día no puede ser modificado.'.format(
                Periodo.get_url_date_period(fecha)
            ))

        return render(request, template, context)
    
    #check delete clockings permissions
    if not request.user.has_perm('scg_app.delete_marcaje'):
        context["lock_delete"] = True

    #check recalculate permission
    if not request.user.has_perm('scg_app.recalculate_blocks'):
        context["lock_recalculate"] = True
        context["lock_add"] = True

    #check add clocking permission
    if not request.user.has_perm('scg_app.add_marcaje'):
        context["lock_add"] = True

    if request.method == 'POST':

        #check recalculate_blocks permission
        if not request.user.has_perm('scg_app.recalculate_blocks'):
            messages.error(
                request, "No tiene permisos para recalcular el día")
            return render(request, template, context)

        if 'recalcular' in request.POST:
            # recalculate blocks
            if not BloqueDePresencia.recalcular_bloques(empleado, fecha):
                messages.error(request, "Hubo un error recalculando el día.")
                return render(request, template, context)

            #update status
            [clase.update_status() for clase in day_classes]

            day_blocks = BloqueDePresencia.objects.filter(
                empleado__pk=id_empleado, fecha=fecha
            ).order_by('inicio')
            context["day_blocks"] = day_blocks
            messages.success(
                request, "Se recalcularon las clases y bloques del día.")
            return render(request, template, context)

        #check add clocking permission
        if not request.user.has_perm('scg_app.add_marcaje'):
            messages.error(request, "No tiene permiso para agregar marcajes.")
            return render(request, template, context)

        #check valid form
        if not form.is_valid():
            messages.error(request, "Error de formulario.")
            return render(request, template, context)

        if not form.cleaned_data["hora_marcaje"]:
            messages.error(
                request, "Ingrese un horario para agregar el marcaje.")
            return render(request, template, context)

        hora_marcaje = form.cleaned_data["hora_marcaje"].replace(second=0)

        #clocking exists
        if Marcaje.objects.filter(
                fecha=fecha, hora=hora_marcaje, empleado=empleado):
            messages.error(request, "Ya existe un marcaje en este horario.")
            return render(request, template, context)

            
        try:    #trying save cloocking
            nuevo_marcaje = Marcaje()
            nuevo_marcaje.empleado = empleado
            nuevo_marcaje.fecha = fecha
            nuevo_marcaje.hora = hora_marcaje
            nuevo_marcaje.save()
        except:
            messages.error(request, "Hubo un error agregando el marcaje.")
            return render(request, template, context)

        # recalculate blocks
        if not BloqueDePresencia.recalcular_bloques(empleado, fecha):
            messages.error(request, "Hubo un error recalculando el día.")
            return render(request, template, context)

        #update status
        [clase.update_status() for clase in day_classes]

        #refresh context
        day_blocks = BloqueDePresencia.objects.filter(
            empleado__pk=id_empleado, fecha=fecha).order_by('inicio')
        context["day_blocks"] = day_blocks
        messages.success(request, "Marcaje agregado y día recalculado.")

    return render(request, template, context)

###################
### front pulls ###
###################

@user_passes_test(check_admin)
def get_nt_empleados(request, context=None):
    """ use pull_netTime() for get all employees from netTime webservice """

    try: 
        Empleado.update_from_nettime()  # internal method
        messages.success(request, "Se actualizaron empleados desde netTime.")

    except ConnectionError:
        messages.error(
            request,
            "No se pudo establecer conexión con el servidor de netTime.")

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
        messages.error(
            request,
            "No se pudo establecer conexión con el servidor de netTime.")

    except Exception as error:
        messages.error(request, f"{error}")

    return redirect('index')


@user_passes_test(check_admin)
def get_nt_incidencias(request, context=None):
    """ use pull_netTime() for get all MotivoAusencia's from netTime 
        webservice """

    try:
        MotivoAusencia.update_from_nettime()
        messages.success(
            request, "Se actualizaron los motivos de ausencia desde NetTime.")

    except ConnectionError:
        messages.error(
            request,
            "No se pudo establecer conexión con el servidor de netTime.")

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
