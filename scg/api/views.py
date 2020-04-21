from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db.models import Q
from scg_app.models import *
import datetime
from collections import defaultdict


# class EmployeeAutocomplete(autocomplete.Select2QuerySetView):
#     def get_queryset(self):
#         #Don't forget to filter out results depending on the visitor !
#         if not self.request.user.is_authenticated:
#             return Empleado.objects.none()

#         qs = Empleado.objects.all()

#         if self.q:
#             qs = qs.filter(nombre__icontains=self.q)

#         return qs

@login_required
def get_clases_from_certificado(request, certificado_id:int, context=None):
    try:
        cert = Certificado.objects.get(pk=certificado_id)
        results = [{
            'empleado': clase.empleado.__str__(),
            'actividad': clase.actividad.nombre,
            'dia_semana': clase.get_dia_semana_display(),
            'fecha': clase.fecha,
            'horario_desde': clase.horario_desde.strftime("%H:%M"),
            'horario_hasta': clase.horario_hasta.strftime("%H:%M"),
            'ausencia': clase.ausencia.__str__() if clase.ausencia else "",
        } for clase in cert.clases.all().order_by('fecha')]

        return JsonResponse({"results": results})
    except:
        return JsonResponse({"results": []})

@login_required
def get_day_classes(request, context=None):
    clases = Clase.objects.filter(fecha__gte=datetime.date.today())

    data = defaultdict(int)
    for clase in clases:
        data[clase.actividad.nombre] += 1

    data_serialize = [{"label": k, "cantidad": v} for k,v in data.items()]
    return JsonResponse({"results": data_serialize})


#@login_required
def get_model_data(_model, _filter, _fields='__all__', _order='id'):#, context=None):
    """ return qs of an specific model from database """

    query = Q()
    if _fields == '__all__':
        search_fields = [field.name for field in _model._meta.fields]
    else:
        search_fields = [field for field in _fields]

    for field in search_fields:
        for data in _filter.split():
            query.add(Q(**{
                f'{field}__icontains': data
            }), Q.OR)

    return _model.objects.filter(query).order_by(_order)

@login_required
def get_empleados(request, _filter, context=None):
    """ return employees what match with filter in JSON format """

    #get queryset objects
    empleados = get_model_data(Empleado, _filter, _order='apellido')

    #list of dict (id: id, text: __str__)
    results = [{
        "id": empleado.id,
        "text": empleado.__str__(),
    } for empleado in empleados]
    
    #context["results"] = results
    return JsonResponse({"results":results})    #resumed context

@login_required
def get_actividades(request, _filter, context=None):
    """ return activitys what match with filter in JSON format """

    actividades = get_model_data(Actividad, _filter, _fields=('nombre', 'grupo__nombre'), _order='nombre')

    results = [{
        "id": actividad.id,
        "text": actividad.__str__(),
    } for actividad in actividades]
    
    return JsonResponse({"results":results})

@login_required
def get_sedes(request, _filter, context=None):
    """ return activitys what match with filter in JSON format """

    sedes = get_model_data(Sede, _filter, _fields=('nombre',), _order='nombre')

    results = [{
        "id": sede.id,
        "text": sede.__str__(),
    } for sede in sedes]
    
    return JsonResponse({"results":results})