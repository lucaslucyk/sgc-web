# -*- coding: utf-8 -*-

### built-in ###
#...

### third ###
from rest_framework import serializers

### django ###
from django.contrib.auth.models import User, Group

### own ###
from scg_app import models

### example ###
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups', 'sedes']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
### example ###

class GrupoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.GrupoActividad
        fields = ['nombre']

class EscalaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Escala
        fields = ['nombre', 'monto_hora', 'grupo']


class TipoLiquidacionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.TipoLiquidacion
        fields = ['id_netTime', 'nombre']


class TipoContratoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.TipoContrato
        fields = ['id_netTime', 'nombre']


class EmpleadoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Empleado
        fields = [
            'id_netTime', 'dni', 'apellido', 'nombre', 'legajo',
            'empresa', 'tipo', 'liquidacion', 'escala',
        ]


class ActividadSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Actividad
        fields = ['nombre', 'grupo']


class MotivoAusenciaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.MotivoAusencia
        fields = ['id_netTime', 'nombre', 'genera_pago']


class SedeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Sede
        fields = ['id_netTime', 'nombre', 'tipo']


class RecurrenciaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Recurrencia
        fields = [
            'fecha_desde', 'fecha_hasta', 'horario_desde', 'horario_hasta',
            'empleado', 'actividad', 'sede', 'get_dias_str', 'locked'
        ]

class ClaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Clase
        fields = [
            'get_dia_semana_display', 'fecha', 'horario_desde', 'horario_hasta',
            'empleado', 'reemplazo', 'sede', 'actividad', 'horas', 'monto',
            'get_estado_display', 'get_presencia_display', 'comentario',
            'ausencia', 'recurrencia', 'confirmada', 'modificada',
            'certificado_set', 'locked',
        ]


class SaldoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Saldo
        fields = [
            'actividad', 'sede', 'desde', 'hasta', 'saldo_asignado',
            'saldo_disponible',
        ]


class MarcajeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Marcaje
        fields = ['empleado', 'fecha', 'hora', 'locked']


class BloqueDePresenciaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.BloqueDePresencia
        fields = ['empleado', 'fecha', 'inicio', 'fin']


class CertificadoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Certificado
        fields = ['clases', 'file', 'motivo', 'locked', 'filename']


class PeriodoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Periodo
        fields = ['desde', 'hasta', 'bloqueado']


class ComentarioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Comentario
        fields = ['fecha', 'hora', 'get_accion_display', 'contenido', 'locked']


# class EmpleadooSerializer(serializers.Serializer):
#     id_netTime = serializers.IntegerField()
#     apellido = serializers.CharField()
#     nombre = serializers.CharField()
#     dni = serializers.CharField()
#     legajo = serializers.CharField()
#     empresa = serializers.CharField()



