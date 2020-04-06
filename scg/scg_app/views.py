import datetime
import re
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.shortcuts import render, redirect, reverse, get_object_or_404
from requests.exceptions import ConnectionError, HTTPError
from scg_app.forms import *
from scg_app.models import *
from zeep import Client
from django.contrib import messages

from django.core.paginator import EmptyPage, Paginator
from django.views.generic.list import ListView
from collections import defaultdict

# Create your views here.
def check_admin(user):
   return user.is_superuser

@login_required
def index(request):
    context = {"empleados": Empleado.objects.all()}

    #contador de visitas, por la variable sesion 
    #(cookies, se elimina al desloguear)
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    context['num_visits'] = num_visits

    return render(request, "scg_app/index.html", context)

def about(request): return render(request, "scg_app/about.html", {})

class SafePaginator(Paginator):
    def validate_number(self, number):
        try:
            return super(SafePaginator, self).validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise

class ClasesView(ListView):
    model = Clase
    template_name = 'scg_app/clases.html'
    context_object_name = 'clases_list'

    #paginator_class = SafePaginator
    #paginate_by = 25

    #ordering = ['fecha']

    def post(self, request, *args, **kwargs):
        #returns get view for process all filters
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        order_by = self.request.GET.get('order_by')
        qs = Clase.objects.filter(fecha__gte=datetime.date.today()).order_by(order_by or 'fecha')

        if self.request.method == 'POST':
            ### if called search button on classes_view ###
            
            form = FiltroForm(self.request.POST)
            if not form.is_valid():
                messages.warning(self.request, "Datos no válidos.")
                return Clase.objects.none()

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

            #add all the filters with and critery
            query = Q()
            [query.add(v, Q.AND) for k, v in querys.items()]
            qs = Clase.objects.filter(query).order_by(order_by or 'fecha')

            #self.context["form"] = form¿

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
        if 'gestion_ausencia' in request.POST:
            ids = get_ids(request.POST.keys())
            if not ids:
                messages.error(request, "Debe seleccionar uno o más registros para gestionar una ausencia.")
                return redirect('clases_view')
            return redirect('gestion_ausencia', ids_clases='-'.join(ids))

        if 'asignar_reemplazo' in request.POST:
            ids = get_ids(request.POST.keys())
            if len(ids) != 1: 
                messages.error(request, "Debe seleccionar -solo- un registro para asignar un reemplazo.")
                return redirect('clases_view')
            return redirect('asignar_reemplazo', id_clase=ids[0])

        if 'confirmar_clases' in request.POST:
            ids = get_ids(request.POST.keys())
            if not ids:
                messages.error(request, "Debe seleccionar una o más clases para confirmarlas.")
                return redirect('clases_view')

            success, error = confirmar_clases(ids)
            messages.success(request, f'Se {"confirmaron" if success > 1 else "confirmó"} {success} clase(s).') if success else None
            messages.error(request, f'No se {"pudieron" if error > 1 else "pudo"} confirmar {error} clase(s) porque esta(n) cancelada(s).') if error else None

            return redirect('clases_view')

        if 'gestion_recurrencia' in request.POST:

            ids = get_ids(request.POST.keys())
            if len(ids) != 1:
                messages.error(request, "Debe seleccionar -solo- una clase para gestionar su programación.")
                return redirect('clases_view')

            messages.warning(request, "Acción aún no implementada.")
            return redirect('clases_view')

        if 'gestion_marcajes' in request.POST:

            ids = get_ids(request.POST.keys())
            if len(ids) != 1:
                messages.error(request, "Debe seleccionar -solo- una clase para ver los marcajes del día.")
                return redirect('clases_view')

            # get the class if all verifications were correct
            clase = get_object_or_404(Clase, pk=ids[0])
            return redirect('gestion_marcajes', id_empleado=clase.empleado.id, fecha=clase.fecha)

    # if accessed by url or method is not POST
    messages.error(request, "La vista no soporta el método GET.")
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
        return render(request, "scg_app/gestion_ausencia.html", context)

    form = MotivoAusenciaForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    clases_to_edit = Clase.objects.filter(pk__in=ids_clases.split('-'))
    context["clases_to_edit"] = clases_to_edit

    if request.method == 'POST':
        if form.is_valid():
            motivo_ausencia = form.cleaned_data["motivo"]

            if not motivo_ausencia:
                #context["status"] = "Seleccione un reemplazante."
                messages.error(request, "Seleccione un Motivo de ausencia.")
                return render(request, "scg_app/gestion_ausencia.html", context)

            for clase in clases_to_edit:
                clase.ausencia = motivo_ausencia
                if not clase.reemplazo: 
                    clase.estado = settings.ESTADOS_CHOICES[3][0]
                clase.save()

            messages.success(request, "Ausencias cargadas correctamente.")

    return render(request, "scg_app/gestion_ausencia.html", context)

@login_required
def asignar_reemplazo(request, id_clase=None, context=None):

    form = ReemplazoForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    if not id_clase:
        return render(request, "scg_app/gestionar_reemplazos.html", context)

    clase_to_edit = get_object_or_404(Clase, pk=id_clase)
    context["clase_to_edit"] = clase_to_edit

    if request.method == 'POST':
        #form = ReemplazoForm(request.POST)
        if form.is_valid():
            reemplazante = form.cleaned_data["reemplazo"]

            if not reemplazante:
                #context["status"] = "Seleccione un reemplazante."
                messages.error(request, "Seleccione un reemplazante.")
                return render(request, "scg_app/gestionar_reemplazos.html", context)

            if clase_to_edit.empleado == reemplazante:
                messages.error(request, "El reemplazante no puede ser el empleado asignado.")
                return render(request, "scg_app/gestionar_reemplazos.html", context)

            if reemplazante.is_busy(fecha=clase_to_edit.fecha, inicio=clase_to_edit.horario_desde, fin=clase_to_edit.horario_hasta):
                messages.error(request, "El reemplazante no está disponible en el rango horario de esta clase.")
                return render(request, "scg_app/gestionar_reemplazos.html", context)

            clase_to_edit.reemplazo = reemplazante
            clase_to_edit.estado = settings.ESTADOS_CHOICES[2][0]
            clase_to_edit.save()

            messages.success(request, "Reemplazo cargado con éxito!")

    return render(request, "scg_app/gestionar_reemplazos.html", context)

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
        return render(request, "scg_app/gestion_marcajes.html", context)

    empleado = Empleado.objects.filter(pk=id_empleado)
    if not empleado:
        messages.error(request, "El empleado no existe")
        return render(request, "scg_app/gestion_marcajes.html", context)

    empleado = empleado[0] #checked what exists
    day_classes = Clase.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('horario_desde')
    day_blocks = BloqueDePresencia.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('inicio')
    day_clockings = Marcaje.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('entrada')

    context["day_classes"] = day_classes
    context["day_blocks"] = day_blocks
    #context["day_clockings"] = day_clockings

    if request.method == 'POST':

        if 'delete_marcaje' in request.POST:
            messages.warning(request, "Acción aún no soportada..")
            return render(request, "scg_app/gestion_marcajes.html", context)

        if not form.is_valid():
            messages.error(request, "Error de formulario.")
            return render(request, "scg_app/gestion_marcajes.html", context)

        hora_marcaje = form.cleaned_data["hora_marcaje"].replace(second=0)

        #marc_exists = Marcaje.objects.filter(hora=hora_marcaje)
        if Marcaje.objects.filter(hora=hora_marcaje):   #clocking exists
            messages.error(request, "Ya existe un marcaje en este horario.")
            return render(request, "scg_app/gestion_marcajes.html", context)

        
        try:    #trying save cloocking
            nuevo_marcaje = Marcaje()
            nuevo_marcaje.empleado = empleado
            nuevo_marcaje.fecha = fecha
            nuevo_marcaje.hora = hora_marcaje
            nuevo_marcaje.save()
        except:
            messages.error(request, "Hubo un error agregando el marcaje.")
            return render(request, "scg_app/gestion_marcajes.html", context)

        # recalculate blocks
        if not BloqueDePresencia.recalcular_bloques(empleado, fecha):
            messages.error(request, "Hubo un error recalculando el día.")
            return render(request, "scg_app/gestion_marcajes.html", context)

        messages.success(request, "El marcaje se ha agregado y el día se ha recalculado correctamente.")
        day_blocks = BloqueDePresencia.objects.filter(empleado__pk=id_empleado, fecha=fecha).order_by('inicio')
        context["day_blocks"] = day_blocks

    return render(request, "scg_app/gestion_marcajes.html", context)


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
        context['status'] = "Tabla de empleados importada correctamente!" if emp_records_init < Empleado.objects.count() else "Datos de empleados actualizados correctamente!"
    else: context['status'] = empleados_db
    return render(request, "scg_app/pull_empleados.html", context)

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
    else: context['status'] = sedes_db
    return render(request, "scg_app/pull_sedes.html", context)

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

@login_required
def programar_clase(request, context=None):
    form = ProgRecurrenciaForm()
    context = context or {'form': form}
    saldos = Saldo.objects
    if request.method == 'POST':
        form = ProgRecurrenciaForm(request.POST)
        if form.is_valid():
            fields = {
            "dia_semana": form.cleaned_data["dia_semana"], 
            "fecha_desde": form.cleaned_data["fecha_desde"], 
            "fecha_hasta": form.cleaned_data["fecha_hasta"], 
            "horario_desde": form.cleaned_data["horario_desde"].replace(second=0, microsecond=0),  #limpiando segundos innecesarios
            "horario_hasta": form.cleaned_data["horario_hasta"].replace(second=0, microsecond=0),  #limpiando segundos innecesarios
            "actividad": form.cleaned_data["actividad"], 
            "sede": form.cleaned_data["sede"], 
            "empleado": form.cleaned_data["empleado"], 
            }

            context["form"] = form
            
            if fields["fecha_hasta"] >= datetime.datetime.now().date() and not settings.DEBUG:
                context["status"] = ["No se pueden crear recurrencias para fechas pasadas."]
                return render(request, "scg_app/programar_clase.html", context)

            if fields["horario_desde"] >= fields["horario_hasta"]:
                context["status"] = ["La hora de fin debe ser mayor a la de inicio."]
                return render(request, "scg_app/programar_clase.html", context)

            if fields["fecha_desde"] >= fields["fecha_hasta"]:
                context["status"] = ["La fecha de fin debe ser mayor a la de inicio."]
                return render(request, "scg_app/programar_clase.html", context)

            

            #recurrencia objects
            new_recurrencia = Recurrencia.objects
            if not check_recs_unique(fields, new_recurrencia):
                context["status"] = ["No se creo la recurrencia, por encontrarse una recurrencia igual previamente creada!"]
                return render(request, "scg_app/programar_clase.html", context)

            if saldos.filter(actividad=fields["actividad"], sede=fields["sede"], year=fields["fecha_desde"].year).exists():

                for dia in fields["dia_semana"]:
                    if Recurrencia.in_use(
                        employee=fields["empleado"],
                        week_day=dia,
                        date_ini=fields["fecha_desde"],
                        date_end=fields["fecha_hasta"],
                        hour_ini=fields["horario_desde"],
                        hour_end=fields["horario_hasta"]
                    ):
                        fields["dia_semana"].remove(dia)
                
                if not fields["dia_semana"]:
                    context["status"] = ["Todos los días estan cubiertos por otras recurrencias."]
                    return render(request, "scg_app/programar_clase.html", context)

                for dia in fields["dia_semana"]:

                    new_recurrencia.update_or_create(
                        id=None, 
                        dia_semana=dia, 
                        fecha_desde=fields["fecha_desde"], 
                        fecha_hasta=fields["fecha_hasta"], 
                        horario_desde=fields["horario_desde"], 
                        horario_hasta=fields["horario_hasta"], 
                        empleado=fields["empleado"], 
                        actividad=fields["actividad"], 
                    )
                    test = generar_clases(fields, dia)

                if test[0]:
                    if len(test[1]) == 0: context["status"] = ["Recurrencia creada junto con sus clases!"]
                    else: context["status"] = [f"Recurrencia creada! Algunas clases no se crearon ({str(len(test[1]))}) por estar previamente creadas"] #no esta entrando aca abajo, pero si funciona como deberia, a debuguear
                    saldo_restante = recalcular_saldo(fields)
                    if saldo_restante and saldo_restante < 0: context["status"].append(["Atencion! Saldo de clases negativo!"])
                    return render(request, "scg_app/programar_clase.html", context)
                else:
                    context["status"] = ["Recurrencia creada, pero no se crearon clases puntuales!"]
                    return render(request, "scg_app/programar_clase.html", context)
            else:
                context["status"] = [f'No se pueden crear clases de {fields["actividad"]} hasta no agregar saldos validos en la sede {fields["sede"]}!']
                return render(request, "scg_app/programar_clase.html", context)

        else: context['form'] = form
    return render(request, "scg_app/programar_clase.html", context)

def recalcular_saldo(f):
    saldos, clases, recurrencia = Saldo.objects, Clase.objects, Recurrencia.objects
    sub_saldo = saldos.filter(actividad=f["actividad"], sede=f["sede"], year=f["fecha_desde"].year)
    if len(sub_saldo) == 1: #trabajado sobre la CERTEZA que, para cada saldo, solo hay 1 combinacion de 1) actividad, 2) sede y 3) año
        target_saldo = sub_saldo[0]
        if 0 == target_saldo.saldo_actual or target_saldo.saldo_actual > target_saldo.saldo_inicial: target_saldo.saldo_actual = target_saldo.saldo_inicial
        periodos = target_saldo.get_periodo_display() #hackazo con "{model}.get_{atribute}_display()!!
        periodos = [datetime.datetime.strptime(p, '%d/%m').replace(year=datetime.datetime.now().year).date() for p in periodos.split(' al ')]
        sub_clases = clases.filter(fecha__gt=periodos[0], actividad=f["actividad"], sede=f["sede"])
        target_saldo.saldo_actual = target_saldo.saldo_inicial - sub_clases.count()
        target_saldo.save()
    return target_saldo.saldo_actual if len(sub_saldo) == 1 else None

def generar_clases(f, dia):
    success = False
    clases, parent = Clase.objects, Recurrencia.objects
    clase_record_list = clases.count()
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    dias_delta = f["fecha_hasta"] - f["fecha_desde"]
    cant_creadas, clases_list, rejected, clase_temp = 0, [], [], []
    
    #emple = Empleado.objects.get(id=f["empleado"])

    for i in range(dias_delta.days):
        dia_target = f["fecha_desde"] + datetime.timedelta(days=i)
        if dias[dia_target.weekday()] == dia:
            if check_clases_unique(f, clases, i) and not f["empleado"].is_busy(dia_target, f["horario_desde"], f["horario_hasta"]):
                clase_temp = Clase(
                    id=None,
                    parent_recurrencia=parent.latest(), 
                    parent=parent.latest(), 
                    dia_semana=dia, 
                    fecha=dia_target, 
                    horario_desde=f["horario_desde"], 
                    horario_hasta=f["horario_hasta"], 
                    actividad=f["actividad"], 
                    sede=f["sede"], 
                    empleado=f["empleado"], 
                    estado=settings.ESTADOS_CHOICES[0][-1], 
                    presencia=None, 
                )
                clases_list.append(clase_temp) if type(clase_temp) != list else None
            else: rejected.append(clase_temp) if type(clase_temp) != list else None
        clase_temp = []

    cant_creadas = len(clases_list)
    clases.bulk_create(clases_list)
    if clase_record_list < clases.count(): success = True
    return [success, rejected, cant_creadas]

def check_recs_unique(f, recurrencia):
    success = False
    for dia in f["dia_semana"]:
        rec_filter_results = recurrencia.filter(
            dia_semana=dia, 
            fecha_desde=f["fecha_desde"], 
            fecha_hasta=f["fecha_hasta"], 
            horario_desde=f["horario_desde"], 
            horario_hasta=f["horario_hasta"], 
            empleado=f["empleado"], 
            actividad=f["actividad"], 
        )
        if len(rec_filter_results) == 0: success = True
        else:
            success = False
            break
    return success

def check_clases_unique(f, clase, i):
    success = False
    for dia in f["dia_semana"]:
        rec_filter_results = clase.filter(
            dia_semana=dia, 
            fecha=f["fecha_desde"] + datetime.timedelta(days=i), 
            horario_desde=f["horario_desde"], 
            horario_hasta=f["horario_hasta"],
            actividad=f["actividad"], 
            sede=f["sede"], 
            empleado=f["empleado"], 
        )
        if len(rec_filter_results) == 0: success = True
        else:
            success = False
            break
    return success

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

@user_passes_test(check_admin)
def modificar_estado(request): #admin-only conflict-resolver tool
    return
