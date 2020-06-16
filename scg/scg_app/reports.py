# -*- coding: utf-8 -*-
""" views for custom reports """

### built-in ###
from collections import defaultdict
import json
import os

### third ###
import pandas as pd

### django ###
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.forms.models import model_to_dict
from django.contrib import messages
from django.core.files import File

### own ###
from django.conf import settings
from scg_app import models

def json_to_rows(data_json):
    pass


def excel_in_tmp(data: list, filename='hardcoded.xlsx', *args, **kwargs):
    """ 
    Generate excel response with 'data' info in environ 'tmp'
    - Parameters:
        - 'data':
        [{'sheet_name': str, 'header': list, 'index': bool, 'data': list}, ]

    - Return: fileurl (path + filename)
    """
    tmp_dir = settings.TMP_DIR
    file_dir = os.path.join(tmp_dir, filename)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(file_dir, engine='xlsxwriter')

    # Write each dataframe to a different worksheet.
    for sheet in data:
        df = pd.DataFrame(sheet.get('data'))
        df.to_excel(
            writer,
            sheet_name=sheet.get('sheet_name'),
            header=sheet.get('header'),
            index=sheet.get('index'),
        )
    
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    return file_dir


    # generate excel response type
    # response = HttpResponse(
    #     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    #     charset='iso-8859-1')
    # response['Content-Disposition'] = f'attachment; filename={filename}'

    # #convert data to Pandas DataFrame and write in excel response
    # for sheet in data:
    #     df = pd.DataFrame(sheet.get('data'))
    #     df.to_excel(
    #         response,
    #         sheet_name=sheet.get('sheet_name'),
    #         header=sheet.get('header'),
    #         index=sheet.get('index'),
    #         engine='xlsxwriter',
    #     )
    
    # return response

def generate_excel(data_list, sheet_name='SGC-APP', header=None, index=False):
    """ Generate excel response from data_list recived """

    # generate excel response type
    response = HttpResponse(
        content_type='application/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        charset='iso-8859-1')
    response['Content-Disposition'] = f'attachment; filename=liquidacion.xlsx'
    
    #convert data_list to Pandas DataFrame and write in excel response
    df = pd.DataFrame(data_list)
    df.to_excel(response, sheet_name=sheet_name, header=header, index=index)

    return response

@login_required
def liquida_mono(request, pk, context=None):
    periodo = get_object_or_404(models.Periodo, pk=pk)
    if not periodo.bloqueado:
        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> debe estar \
            bloqueado para liquidarlo.'.format(periodo.get_edit_url())
            )
        return redirect('periodos_view')

    contrato = get_object_or_404(models.TipoContrato, nombre='Monotributista')

    clases = models.Clase.objects.filter(
        empleado__tipo=contrato,
        fecha__gte=periodo.desde,
        fecha__lte=periodo.hasta,
        confirmada=True,
    ).exclude(
        estado=settings.ESTADOS_CHOICES[-1][0]
    ).order_by('sede', 'empleado')

    if not clases:
        return JsonResponse(
            {'message': 'No hay clases para liquidar en este periodo.'},
            status=404,
        )

    # process in soc (structure of classes) for get structure like:
    # { sede: { empleado: {actividad.grupo: [clases, ]} }
    soc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for clase in clases:
        soc[clase.sede][clase.empleado][clase.actividad.grupo].append(clase)

    # base prepare
    data_grouped = []
    data_detail = []
    head_group = ['SEDE', 'DNI', 'DNI/SEDE', 'EMPLEADO', 'MONTO']
    head_detail = [
        'CODIGO', 'SEDE', 'DNI', 'DNI/SEDE','EMPLEADO', 'GRUPO DE ACTIVIDAD',
        'HORAS', 'MONTO',
    ]
    
    # data proccess
    for sede, empleado_grupos_clases in soc.items():
        for empleado, grupos_clases in empleado_grupos_clases.items():
            
            # group prepare
            add_to_grouped = [
                sede.nombre.upper(),
                empleado.dni,
                empleado.dni + sede.nombre.upper(),
                str(empleado).upper().replace(',', ''),
                0.0, #update in next step
            ]

            for grupo, clases in grupos_clases.items():
                add_to_detail = [
                    sede.codigo.upper(),
                    sede.nombre.upper(),
                    empleado.dni,
                    empleado.dni + sede.nombre.upper(),
                    str(empleado).upper().replace(',', ''),
                    grupo.nombre.upper(),
                    round(sum(clase.horas for clase in clases), 2),
                    round(sum(clase.monto for clase in clases), 2),
                ]
                data_detail.append(add_to_detail)

                #group mount update
                add_to_grouped[-1] += add_to_detail[-1]
            
            #add total of sede
            data_grouped.append(add_to_grouped)

    # generate excel in tmp directory
    excel_dir = excel_in_tmp(
        data=[{
            'sheet_name': 'Detalle',
            'header': head_detail,
            'index': False,
            'data': data_detail,
        }, {
            'sheet_name': 'Total',
            'header': head_group,
            'index': False,
            'data': data_grouped,
        }],
        filename='liquida_mono.xlsx',
        )
    
    # check if exist a 'liquidacion' for this period
    liquidacion = models.Liquidacion.objects.filter(
        periodo=periodo, tipo=contrato)

    #create if not exist
    if liquidacion:
        liquidacion = liquidacion.first()
    else:
        liquidacion = models.Liquidacion.objects.create(
            periodo=periodo,tipo=contrato)
    
    liquidacion.file.save('liquida_mono.xlsx', File(open(excel_dir, 'rb')))

    return JsonResponse({'fileUrl': liquidacion.file.url})

@login_required
def liquida_rd(request, pk, context=None):
    """ return excel with RD liquidation format """

    periodo = get_object_or_404(models.Periodo, pk=pk)
    if not periodo.bloqueado:
        messages.error(
            request,
            'El <a href="{}" class="no-decore">periodo</a> debe estar \
            bloqueado para liquidarlo.'.format(periodo.get_edit_url())
        )
        return redirect('periodos_view')

    contrato = get_object_or_404(
        models.TipoContrato, nombre='Relación de Dependencia')

    clases = models.Clase.objects.filter(
        empleado__tipo=contrato,
        fecha__gte=periodo.desde,
        fecha__lte=periodo.hasta,
        confirmada=True,
    ).exclude(
        #cancelled
        estado=settings.ESTADOS_CHOICES[-1][0]
    ).order_by('empleado', 'fecha', 'horario_desde', 'horario_hasta')

    if not clases:
        return JsonResponse(
            {'message': 'No hay clases para liquidar en este periodo.'},
            status=404,
        )

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
            clase.format_user_comments,
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
                clase.format_user_comments,
            ])

    # generate excel in tmp directory
    excel_dir = excel_in_tmp(
        data=[{
            'sheet_name': 'Presentismo RD',
            'header': header,
            'index': False,
            'data': data_list,
        }],
        filename='liquida_rd.xlsx',
    )

    # check if exist a 'liquidacion' for this period
    liquidacion = models.Liquidacion.objects.filter(
        periodo=periodo, tipo=contrato)

    #create if not exist
    if liquidacion:
        liquidacion = liquidacion.first()
    else:
        liquidacion = models.Liquidacion.objects.create(
            periodo=periodo, tipo=contrato)

    liquidacion.file.save('liquida_rd.xlsx', File(open(excel_dir, 'rb')))

    return JsonResponse({'fileUrl': liquidacion.file.url})

    # generate and return excel
    #return generate_excel(data_list, sheet_name='Presentismo RD', header=header)
