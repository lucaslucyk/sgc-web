# -*- coding: utf-8 -*-
""" views for custom reports """
### built-in ###
from collections import defaultdict
import json

### third ###
import pandas as pd

### django ###
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.forms.models import model_to_dict
from django.contrib import messages

### own ###
from django.conf import settings
from scg_app import models

def json_to_rows(data_json):
    pass

def generate_excel(data_list, sheet_name='SGC-APP', header=None, index=False):
    """ Generate excel response from data_list recived """

    # generate excel response type
    response = HttpResponse(
        content_type='application/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        charset='iso-8859-1')
    response['Content-Disposition'] = f'attachment; filename=testing.xlsx'
    
    #convert data_list to Pandas DataFrame and write in excel response
    df = pd.DataFrame(data_list)
    df.to_excel(response, sheet_name=sheet_name, header=header, index=index)

    return response

@login_required
def liquida_mono(request, pk, format='excel', context=None):
    periodo = get_object_or_404(models.Periodo, pk=pk)
    if not periodo.bloqueado:
        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> debe estar \
            bloqueado para liquidarlo.'.format(periodo.get_edit_url())
            )
        return redirect('periodos_view')

    clases = models.Clase.objects.filter(
        empleado__tipo__nombre='Monotributista',
        fecha__gte=periodo.desde,
        fecha__lte=periodo.hasta,
        confirmada=True,
    ).exclude(
        estado=settings.ESTADOS_CHOICES[-1][0]
    ).order_by('sede', 'empleado')

    # process in soc for get structure like:
    # { sede: { empleado: {actividad.grupo: [clases, ]} }
    soc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for clase in clases:
        soc[clase.sede][clase.empleado][clase.actividad.grupo].append(clase)

    # base prepare
    data_list = []
    headers = [
        'CODIGO', 'SEDE', 'DNI', 'DNI/SEDE','EMPLEADO', 'GRUPO DE ACTIVIDAD',
        'HORAS', 'MONTO',
    ]

    # data proccess
    for sede, empleado_grupos_clases in soc.items():
        for empleado, grupos_clases in empleado_grupos_clases.items():
            for grupo, clases in grupos_clases.items():
                data_list.append([
                    sede.codigo.upper(),
                    sede.nombre.upper(),
                    empleado.dni,
                    empleado.dni + sede.nombre.upper(),
                    str(empleado).upper().replace(',', ''),
                    grupo.nombre.upper(),
                    round(sum(clase.horas for clase in clases), 2),
                    round(sum(clase.monto for clase in clases), 2),
                ])

    # generate and return excel
    return generate_excel(data_list, sheet_name='Presentismo', header=headers)


    # employee_fields = models.Empleado.serializable_fields()
    # structure = list()
    # for empleado, sedes_grupos_clases in soc.items():
    #     structure.append({
    #         'empleado': model_to_dict(empleado, fields=employee_fields),
    #         'values': [],
    #     })

    #     for sede, grupos_clases in sedes_grupos_clases.items():
    #         structure[-1]['values'].append({
    #             'sede': model_to_dict(sede, exclude=['id', 'id_netTime']),
    #             'values': []
    #         })

    #         for grupo, clases in grupos_clases.items():
    #             structure[-1]['values'][-1]['values'].append({
    #                 'grupo': model_to_dict(grupo, exclude=['id', 'id_netTime']),
    #                 'horas': round(sum(clase.horas for clase in clases), 2),
    #                 'monto': round(sum(clase.monto for clase in clases), 2),
    #             })

    # return JsonResponse({"results": structure})

@login_required
def liquida_rd(request, pk, format='excel', context=None):
    """ return excel with RD liquidation format """

    periodo = get_object_or_404(models.Periodo, pk=pk)
    if not periodo.bloqueado:
        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> debe estar \
            bloqueado para liquidarlo.'.format(periodo.get_edit_url())
        )
        return redirect('periodos_view')

    clases = models.Clase.objects.filter(
        empleado__tipo__nombre='Relación de Dependencia',
        fecha__gte=periodo.desde,
        fecha__lte=periodo.hasta,
        confirmada=True,
    ).exclude(
        #cancelled
        estado=settings.ESTADOS_CHOICES[-1][0]
    ).order_by('empleado', 'fecha', 'horario_desde', 'horario_hasta')

    # base prepare
    data_list = []
    header = [
        'Estado', 'Sede', 'Legajo', 'Apellido, Nombre', 'Actividad',
        'Agrupador', 'Código', 'Tipo', 'Fecha', 'Día', 'Inicio', 'Fin', 'Horas',
        'Ausencia', 'Adjuntos', 'Comentario',
    ]

    for clase in clases:
        data_list.append([
            clase.get_estado_display(),
            clase.sede.nombre.upper(),
            clase.empleado.legajo,
            str(clase.empleado),
            clase.actividad.nombre,
            clase.actividad.grupo.nombre,
            clase.actividad.grupo.codigo,
            clase.actividad.grupo.tipo,
            clase.fecha.strftime("%d/%m/%Y"),
            clase.dia_semana_display,
            clase.horario_desde.strftime("%H:%M"),
            clase.horario_hasta.strftime("%H:%M"),
            clase.horas,
            clase.ausencia.nombre if clase.ausencia else '',
            clase.url_certificados,
            clase.comentario
        ])
        if clase.reemplazo:
            data_list.append([
                'Realizada',    #estado
                clase.sede.nombre.upper(),
                clase.reemplazo.legajo if clase.reemplazo.legajo else '',
                str(clase.reemplazo),
                clase.actividad.nombre,
                clase.actividad.grupo.nombre,
                clase.actividad.grupo.codigo,
                clase.actividad.grupo.tipo,
                clase.fecha.strftime("%d/%m/%Y"),
                clase.dia_semana_display,
                clase.horario_desde.strftime("%H:%M"),
                clase.horario_hasta.strftime("%H:%M"),
                clase.horas,
                '', #ausencia
                clase.url_certificados,
                clase.comentario
            ])

    # generate and return excel
    return generate_excel(data_list, sheet_name='Presentismo RD', header=header)
