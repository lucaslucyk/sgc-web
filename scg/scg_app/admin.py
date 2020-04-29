from django.contrib import admin
from scg_app.models import *

# Register your models here.

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('tipo_rol', )

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    fields = ('id_netTime', 'apellido', 'nombre', 'dni', 'legajo', 'empresa', 
        'escala', 'tipo', 'liquidacion'
    )
    list_display = ('id_netTime', 'apellido', 'nombre', 'dni', 'legajo', 
        'empresa',
    )
    ordering = ('apellido', )
    #readonly_fields = ('apellido', 'nombre', 'dni', 'legajo', 'empresa', )

    def has_delete_permission(self, request, obj=None):
        return True

    # def has_add_permission(self, request, obj=None):
    #    return False

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'id', )
    readonly_fields = ('nombre', 'tipo', 'id', )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo', )#'categoria', )

@admin.register(MotivoAusencia)
class MotivoAusenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'genera_pago' )

@admin.register(Saldo)
class SaldoAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'sede', 'desde', 'hasta', 'saldo_asignado', 
        'saldo_disponible'
    )

@admin.register(Recurrencia)
class RecurrenciaAdmin(admin.ModelAdmin):
    fields = (
        ('fecha_desde', 'horario_desde'), ('fecha_hasta', 'horario_hasta'), 
        'empleado', 'sede', 'actividad', 'weekdays'
    )
    list_display = ('id', 'empleado', 'fecha_desde', 'fecha_hasta', 
        'horario_desde', 'horario_hasta', 'sede', 
        'actividad','get_dias_str'
    )
    list_filter = ['empleado', 'sede', 'actividad']

@admin.register(Clase)
class Clase(admin.ModelAdmin):
    fields = ('parent_recurrencia', ('dia_semana', 'fecha'), 
        ('horario_desde', 'horario_hasta'), 'actividad', 'sede', 'empleado', 
        'modificada', 'estado', 'presencia', 'ausencia', 'reemplazo',
        'confirmada', 'adjunto',
    )

    list_display = (
        'estado', 'presencia', 'empleado', 'reemplazo', 'sede',
        'actividad', 'dia_semana', 'fecha', 'horario_desde', 'horario_hasta',
        'modificada', 'ausencia', 'confirmada',
    )

    readonly_fields = ('parent_recurrencia', 'creacion', 'dia_semana', 'fecha',
        'horario_desde', 'horario_hasta', 'actividad', 'sede', 'empleado', 
        'modificada', 'presencia', 'ausencia', 'reemplazo', 'estado',
        #'estado',
    )

    #def has_delete_permission(self, request, obj=None):
    #   return False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Marcaje)
class MarcajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'fecha', 'hora')

@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto_hora', )

@admin.register(GrupoActividad)
class GrupoActividad(admin.ModelAdmin):
    list_display = ('nombre', )

admin.site.register(BloqueDePresencia)
admin.site.register(Certificado)
admin.site.register(TipoLiquidacion)
admin.site.register(TipoContrato)