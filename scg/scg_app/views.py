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

    #contador de visitas, por la variable sesion (cookies, se elimina al desloguear)
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

    paginator_class = SafePaginator
    paginate_by = 25

    def post(self, request, *args, **kwargs):
        #returns get view for process all filters
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        qs = Clase.objects.filter(fecha__gte=datetime.date.today()).order_by('fecha')

        if self.request.method == 'POST':
            
            form = FiltroForm(self.request.POST)
            if not form.is_valid():
                #print("not valid form")
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

            print(dia_semana)
            
            querys = defaultdict(Q)

            ### searchs ###
            if data_emple or data_reemplazo:
                for field in Empleado._meta.fields:
                    if data_emple:
                        querys["empleado"].add(Q(**{f'empleado__{field.name}__icontains': data_emple}), Q.OR)
                    if data_reemplazo:
                        querys["reemplazo"].add(Q(**{f'reemplazo__{field.name}__icontains': data_reemplazo}), Q.OR)

            if data_actividad:
                querys["actividad"].add(Q(**{f'actividad__nombre__icontains': data_actividad}), Q.OR)
                querys["actividad"].add(Q(**{f'actividad__grupo__nombre__icontains': data_actividad}), Q.OR)

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
            if hora_inicio != "00:00":
                querys["hora_inicio"] = Q(horario_hasta__gte=hora_inicio)
            if hora_fin != "23:59":
                querys["hora_fin"] = Q(horario_desde__lt=hora_fin)

            ### checks ###
            if solo_ausencia:
                querys["solo_ausencia"] = Q(ausencia__isnull=not solo_ausencia)
            if solo_reemplazos:
                querys["solo_reemplazos"] = Q(reemplazo__isnull=not solo_reemplazos)

            #add all the filters with and critery
            query = Q()
            [query.add(v, Q.AND) for k, v in querys.items()]
            qs = Clase.objects.filter(query).order_by('fecha')

        return qs

    def get_context_data(self, *args, **kwargs):
        
        context = super().get_context_data(*args, **kwargs)
        context["form"] = context.get("form") or FiltroForm(self.request.POST if self.request.method == 'POST' else None)
        return context


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
                    if Recurrencia.is_busy(
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

@login_required
def monitor_clases(request):
    context = {}
    clases, reemplazos, ausencias = Clase.objects.all(), Reemplazo.objects.all(), Ausencia.objects.all()
    entrada = []
    for clase in clases:
        if reemplazos.filter(clase_id=clase.id).exists():
            if ausencias.filter(clase_id=clase.id).exists(): entrada.append({'clase': clase, 'ausencia': ausencias.filter(clase_id=clase.id)[0], 'reemplazo': reemplazos.filter(clase_id=clase.id)[0]})
            else: entrada.append({'clase': clase, 'reemplazo': reemplazos.filter(clase_id=clase.id)[0]})
        else:
            if ausencias.filter(clase_id=clase.id).exists(): entrada.append({'clase': clase, 'ausencia': ausencias.filter(clase_id=clase.id)[0]})
            else: entrada.append(clase)
    context["clases"] = entrada
    return render(request, "scg_app/monitor.html", context)

@login_required
def filtros(request, context=None):
    form = FiltrosForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}
    clases, reemplazos, ausencias, actividades, empleados, marcajes = Clase.objects.all(), Reemplazo.objects.all(), Ausencia.objects.all(), Actividad.objects.all(), Empleado.objects.all(), Marcaje.objects.all()
    # if request.method == 'GET':
    #     print(request.GET)
    #     #for get name of form 
    #     #can be get or post
    #     name = request.GET.get('name')

    if request.method == 'POST':
        #form = FiltrosForm(request.POST)
        #current_user = User.objects.get(pk=request.session.get('_auth_user_id'))

        if 'gestion_ausencia' in request.POST:
            #print([item for item in request.POST.keys()])

            ids = [str(_id.split("_")[-1]) for _id in request.POST.keys() if "confirm" in _id]
            if len(ids) < 1:
                messages.error(request, "Debe seleccionar uno o más registros para gestionar una ausencia.")
                return render(request, "scg_app/filtro_monitor_test.html", context)
            return redirect('gestion_ausencia', ids_clases='-'.join(ids))


        if 'filtrar' in request.POST: #boton de filtrado
            if form.is_valid():
                consultas = clases.filter()
                campos = {
                    "estado": form.cleaned_data["estado"], 
                    "empleado_asignado": form.cleaned_data["empleado_asignado"], 
                    "empleado_ejecutor": form.cleaned_data["empleado_ejecutor"], 
                    "actividad": form.cleaned_data["actividad"], 
                    "fecha_desde": form.cleaned_data["fecha_desde"], 
                    "fecha_hasta": form.cleaned_data["fecha_hasta"], 
                    "dias": form.cleaned_data["dias"], 
                    "horario_desde": form.cleaned_data["horario_desde"], 
                    "horario_hasta": form.cleaned_data["horario_hasta"], 
                    "clases_ausentes": form.cleaned_data["clases_ausentes"], 
                    "clases_reemplazos": form.cleaned_data["clases_reemplazos"], 
                }
                context["form"] = form
                campos = list(campos.items())

                consultas_aux = clases.none()
                if len(campos[6][-1]) > 0: #filtro por dias
                    for i in range(len(campos[6][-1])): consultas_aux = consultas_aux | consultas.filter(dia_semana=campos[6][-1][i])
                    consultas = consultas_aux

                consultas_aux = clases.none()
                if len(campos[0][-1]) > 0: #filtro de estados
                    for i in range(len(campos[0][-1])): consultas_aux = consultas_aux | consultas.filter(estado=settings.ESTADOS_CHOICES[int(campos[0][-1][i])][-1])
                    consultas = consultas_aux

                if campos[1][-1] != None: #filtros por empleados
                    empleado = empleados.filter(nombre=campos[1][-1].nombre)
                    if empleado.exists(): consultas = consultas.filter(empleado=empleado[0].id)

                if campos[3][-1] != None: #filtro por actividad
                    actividad = actividades.filter(nombre=campos[3][-1])
                    if actividad.exists(): consultas = consultas.filter(actividad=actividad[0].id)

                #filtros de fechas/horas
                if campos[4][-1] != None: consultas = consultas.filter(fecha__gte=campos[4][-1])
                if campos[5][-1] != None: consultas = consultas.filter(fecha__lte=campos[5][-1])
                if campos[7][-1] != None: consultas = consultas.filter(horario_desde__gte=campos[7][-1].replace(second=0))
                if campos[8][-1] != None and campos[7][-1] != campos[8][-1]: consultas = consultas.filter(horario_hasta__lte=campos[8][-1].replace(second=0))

                consultas_ausencias = ausencias.none() #filtro para mostrar SOLO ausencias
                filtro_ausencias_ids = [a.id for a in ausencias.filter() if a.id in [c.id for c in consultas]]
                for ausencia_id in filtro_ausencias_ids: consultas_ausencias = consultas_ausencias | ausencias.filter(id=ausencia_id)
                if consultas_ausencias.exists(): context["ausencias"] = consultas_ausencias
                if campos[9][-1]: consultas = consultas_ausencias
                context["ausencias_ids"] = [aus.clase.id for aus in consultas_ausencias]

                consultas_reemplazos = reemplazos.none() #filtro para mostrar SOLO reemplazos
                filtro_reemplazos_ids = [r.id for r in reemplazos.filter() if r.id in [c.id for c in consultas]]
                for reemplazo_id in filtro_reemplazos_ids: consultas_reemplazos = consultas_reemplazos | reemplazos.filter(id=reemplazo_id)
                if consultas_reemplazos.exists(): context["reemplazos"] = consultas_reemplazos
                if campos[10][-1]: consultas = consultas_reemplazos
                context["reemplazos_ids"] = list(zip([rem.clase.id for rem in consultas_reemplazos], [remp.empleado_reemplazante for remp in consultas_reemplazos]))
                print(context["reemplazos_ids"])

                if consultas: context["filtros"] = consultas
                else:
                    context["filtros"] = {}
                    context["status"] = "La busqueda no produjo resultados, intente nuevamente con menos filtros"
                    return render(request, "scg_app/filtro_monitor_test.html", context)
            else: context = {'form': form}

        elif 'confirmar' in request.POST: #boton de confirmacion de clases
            if confirmar_clases(request.POST, clases):
                context["filtros"] = clases.filter()
                context["status"] = "Clases confirmadas con exito!"

        # elif 'reemplazos' in request.POST: #boton de gestion de reemplazos
        #     context["filtros"] = clases.filter()
        #     ids = [int(id.split("_")[-1]) for id in list(request.POST.keys()) if "confirm" in id]
        #     if len(ids) > 1: context["status"] = "Solo se puede registrar 1 reemplazo a la vez!"
        #     elif len(ids) < 1: context["status"] = "Se debe seleccionar 1 clase para poder gestionar el reemplazo!"
        #     else:
        #         request.session['reemplazo_nuevo'] = ids[0]
        #         return redirect("gestionar_reemplazos")
        #     return render(request, "scg_app/filtro_monitor_test.html", context)

        ### testing ###
        elif 'asignar_reemplazo' in request.POST:
            ids = [int(id.split("_")[-1]) for id in list(request.POST.keys()) if "confirm" in id]
            if len(ids) != 1: 
                context["status"] = "Debe seleccionar -solo- un registro para asignar un reemplazo"
                return render(request, "scg_app/filtro_monitor_test.html", context)
            return redirect('asignar_reemplazo', id_clase=ids[0])

        elif 'ausencias' in request.POST: #boton de gestion de ausencias
            context["filtros"] = clases.filter()
            context["status"] = "PLACEHOLDER: ausencias.click"

        elif 'recurrencias' in request.POST: #boton de gestion de recurrencias
            context["filtros"] = clases.filter()
            context["status"] = "PLACEHOLDER: recurrencias.click"

        elif any([re.findall(r'marcaje_\d+', req) for req in request.POST]): #boton de vistas de marcajes
            clase_selected = clases.filter(id=int(list(request.POST.keys())[-1].split("_")[-1]))[0]
            sub_marcajes = marcajes.filter(empleado=clase_selected.empleado, fecha=clase_selected.fecha)
            if len(sub_marcajes) < 1:
                context["filtros"] = clases.filter(fecha__gt=datetime.datetime.today(), fecha__lt=datetime.datetime.today() + datetime.timedelta(days=30))
                context["status"] = "No se registran marcajes para la fecha de la clase seleccionada. Tal vez sea una ausencia?"
            else:
                request.session['clockings'] = [p.id for p in sub_marcajes]
                return redirect("agregar_marcaje")

    else: context["filtros"] = clases.filter(fecha__gt=datetime.datetime.today(), fecha__lt=datetime.datetime.today() + datetime.timedelta(days=30)) #default: mostrar el ultimo mes a partir de "hoy"
    if not("ausencias" in context or "reemplazos" in context):
        context["ausencias"] = [""] #lil ol' bug: dado que el for que consume a 'filtros' tiene 2 subfors para consumir a ausencias y reemplazos...
        context["reemplazos"] = [""] #... si estos son vacios, no renderea entradas en la tabla, a resolver o dejar atado con alambre como esta
    return render(request, "scg_app/filtro_monitor_test.html", context)

@login_required
def agregar_marcaje(request, context=None):
    form = MarcajeForm()
    context = context or {'form': form}

    marcajes, clases = Marcaje.objects.all(), Clase.objects
    today_marcajes = request.session['clockings']
    if today_marcajes:
        today_marcajes = [marcajes.filter(id=tm)[0] for tm in today_marcajes if marcajes.filter(id=tm).exists()] #leve checkeo para no llamar indices inexistentes
        clases_aux = clases.none()
        for m in marcajes: clases_aux = clases_aux | clases.filter(empleado=m.empleado, fecha=m.fecha, horario_desde__gte=m.entrada, horario_hasta__lte=m.salida).order_by('horario_desde') if m.salida else clases.filter(empleado=m.empleado, fecha=m.fecha, horario_desde__gte=m.entrada).order_by('horario_desde')
        if clases_aux: context["clases"] = clases_aux

        context["marcajes"] = today_marcajes
        if request.method == 'POST':
            form = MarcajeForm(request.POST)
            if form.is_valid():
                context["form"] = form
                nuevo_marcaje = form.cleaned_data["nuevo_marcaje"].replace(second=0),
                if recalcular_marcajes(today_marcajes, nuevo_marcaje):
                    context["marcajes"] = marcajes.filter(fecha=today_marcajes[0].fecha, empleado=today_marcajes[0].empleado) #sabiendo que todos los marcajes tienen misma fecha y empleado, podemos tomar el 1ro sin problemas
                    request.session['clockings'] = ""
                    return render(request, "scg_app/agregar_marcaje.html", context)
                else: context['status'] ='Error al agregar el marcaje!!'

            else: context = {'form': form}
    return render(request, "scg_app/agregar_marcaje.html", context)

def recalcular_marcajes(marcajes, nuevo_marcaje):
    success, datas, marcaje_aux = False, [], Marcaje.objects.none()
    for m in marcajes: marcaje_aux = marcaje_aux | Marcaje.objects.filter(id=m.id)
    marcajes = marcaje_aux[:]
    if len(marcajes.filter(entrada=nuevo_marcaje[0])) < 1 and len(marcajes.filter(salida=nuevo_marcaje[0])) < 1: #checkear que no exista previamente
        for marcaje in marcajes:
            if marcaje.salida != None: datas += [marcaje.entrada] + [marcaje.salida]
            else: datas += [marcaje.entrada]
        datas += nuevo_marcaje
        datas = sorted(datas, key=lambda k: k.hour)
        if len(datas) % 2 != 0: datas += [None]
        par, i = list(zip(datas[::2], datas[1::2])), 0
        for i in range(len(marcajes)):
            marcaje_aux = Marcaje.objects.filter(id=marcajes[i].id)[0]
            marcaje_aux.entrada, marcaje_aux.salida = par[i][0], par[i][-1]
            marcaje_aux.save()
        if len(marcajes) < len(par):
            marcaje_extra = Marcaje(
                id=None,
                empleado=marcajes[0].empleado,
                fecha=marcajes[0].fecha,
                entrada=par[-1][0],
                salida=par[-1][-1]
            )
            marcaje_extra.save()
        resultado = compare_clockigns() #update de los clockings, sin update a la db
        success = True
    else: print(f"El marcaje {nuevo_marcaje} ya existia, no se realizaron cambios")
    return success

def confirmar_clases(payload, clases):
    success = False
    clases_temp = clases.none()
    ids = [cid.split("_")[-1] for cid in payload if 'confirm_' in cid]
    for i in ids: clases_temp = clases_temp | clases.filter(id=i)
    for i in ids:
        clase = clases.filter(id=i)[0]
        clase.estado = settings.ESTADOS_CHOICES[1][-1]
        clase.save()
        success = success or (clases.filter(id=i)[0].estado == settings.ESTADOS_CHOICES[1][-1]) #si alguna conversion funciona, da por sentado que todas lo van a hacer ")
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

# class GenericEditView(GenericModelView):
#     def paginate_queryset(self, queryset, page_size):
#         """
#         Paginates a queryset, and returns a page object.
#         """
#         paginator = self.get_paginator(queryset, page_size)
#         page_kwarg = self.kwargs.get(self.page_kwarg)
#         page_query_param = self.request.GET.get(self.page_kwarg)
#         page_number = page_kwarg or page_query_param or 1
#         try:
#             page_number = int(page_number)
#         except ValueError:
#             if page_number == 'last':
#                 page_number = paginator.num_pages
#             else:
#                 msg = "Page is not 'last', nor can it be converted to an int."
#                 raise Http404(_(msg))

#         try:
#             return paginator.page(page_number)
#         except InvalidPage as exc:
#             msg = 'Invalid page (%s): %s'
#             raise Http404(_(msg % (page_number, six.text_type(exc))))

# class ListEditView(GenericModelView):
#     pass


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



# @login_required
# def gestionar_reemplazos(request, context=None):
#     form = ReemplazoForm()
#     context = context or {'form': form}

#     if not (request.session['reemplazo_nuevo']):
#         return render(request, "scg_app/gestionar_reemplazos.html", context)

#     #reemplazos, empleados = Reemplazo.objects.all(), Empleado.objects.all()
#     #id_to_modif = request.session['reemplazo_nuevo']

#     #if clase_to_modif:
#     clase_to_edit = get_object_or_404(Clase, pk=request.session['reemplazo_nuevo'])
#     context["clase_to_edit"] = clase_to_edit

#     if request.method == 'POST':
#         form = ReemplazoForm(request.POST)



#     new_reemplazo = get_object_or_404(Clase, pk=request.session['reemplazo_nuevo']) #Clase.objects.filter(id=new_reemplazo)[0] #se llama reemplazo, pero es una CLASE!!
#     context["new_reemplazo"] = new_reemplazo

#     if request.method == 'POST':
#         form = ReemplazoForm(request.POST)
#         if form.is_valid():
#             reemplazante = form.cleaned_data["reemplazo"]
#             if not(reemplazos.filter(clase=new_reemplazo.id, empleado_reemplazante=new_reemplazo.empleado).exists()):
#                 if new_reemplazo.empleado != reemplazante:
#                     if reemplazante:
#                         new_reemplazo.estado = settings.ESTADOS_CHOICES[2][-1]
#                         new_reemplazo.save()
#                         print(f"creando reemplazo, con clase={new_reemplazo.id}, reemplazante={reemplazante}")
#                         reemplazo = Reemplazo(id=None, clase=new_reemplazo, empleado_reemplazante=reemplazante)
#                         reemplazo.save()
#                         context["status"] = ["Reemplazo agregado con exito!"]
#                         request.session['reemplazo_nuevo'] = ""
#                         return render(request, "scg_app/gestionar_reemplazos.html", context)
#                     else: context["status"] = ["Seleccione algun profesor reemplazante!"]
#                 else:
#                     context["status"] = [f"Por favor, seleccione otro profesor que no sea [{reemplazante}], dado que es el profesor asignado!"]
#             else:
#                 context["status"] = [f"Ya se encuentra un reemplazo registrado para la clase {new_reemplazo.id} y profesor {new_reemplazo.empleado}!"] #dificil llegar a este jaja
#         else: context = {'form': form}

#     #context["reemplazos"] = reemplazos
#     return render(request, "scg_app/gestionar_reemplazos.html", context)

@login_required
def gestionar_ausencias(request, context=None): #PLACEHOLDER
    form = AusenciaForm()
    context = context or {'form': form}
    clases, ausencias, empleados = Clase.objects.all(), Ausencia.objects.all()

    if request.method == 'POST':
        form = AusenciaForm(request.POST)
        if form.is_valid():
            pass
        else: context = {'form': form}
    else: context["ausencias"] = ausencias
    #return render(request, "scg_app/gestionar_reemplazos.html", context)

@login_required
def gestionar_recurrencias(request, context=None):
    return

@user_passes_test(check_admin)
def modificar_estado(request): #admin-only conflict-resolver tool
    return
