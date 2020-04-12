from django.contrib import admin
from scg_app.models import *

# Register your models here.

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('tipo_rol', )

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    fields = ('apellido', 'nombre', 'dni', 'legajo', 'empresa', 'escala', 'tipo', 'liquidacion')
    list_display = ('apellido', 'nombre', 'dni', 'legajo', 'empresa', )
    ordering = ('apellido', )
    #readonly_fields = ('apellido', 'nombre', 'dni', 'legajo', 'empresa', )

    def has_delete_permission(self, request, obj=None):
        return False

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
    list_display = ('actividad', 'year', 'periodo', 'saldo_inicial', 'saldo_actual', 'sede', 'saldo_disponible')

@admin.register(Recurrencia)
class RecurrenciaAdmin(admin.ModelAdmin):
    fields = ('dia_semana', ('fecha_desde', 'horario_desde'), ('fecha_hasta', 'horario_hasta'), 'empleado', )
    list_display = ('id', 'empleado', 'dia_semana', 'fecha_desde', 'fecha_hasta', 'horario_desde', 'horario_hasta', )

@admin.register(Clase)
class Clase(admin.ModelAdmin):
    fields = (('parent_recurrencia', 'parent'), ('fecha', 'dia_semana'), 
        ('horario_desde', 'horario_hasta'), 'actividad', 'sede', 'empleado', 
        'modificada', 'estado', 'presencia', 'ausencia', 'reemplazo',
        'confirmada',
    )
    list_display = ('dia_semana', 'fecha', 'horario_desde', 'horario_hasta', 
        'creacion', 'actividad', 'sede', 'empleado', 'modificada', 'estado',
        'confirmada', 
    )
    readonly_fields = ('parent_recurrencia', 'creacion', 'dia_semana', 'fecha',
        'horario_desde', 'horario_hasta', 'actividad', 'sede', 'empleado', 
        'parent', 'modificada', 'presencia',
        #'estado',
    )

    #def has_delete_permission(self, request, obj=None):
    #   return False

    def has_add_permission(self, request, obj=None):
        return False

# @admin.register(Ausencia)
# class AusenciaAdmin(admin.ModelAdmin):
#     list_display = ('clase', 'motivo', )

# @admin.register(Reemplazo)
# class ReemplazoAdmin(admin.ModelAdmin):
#     list_display = ('clase', 'empleado_reemplazante', )

@admin.register(Marcaje)
class MarcajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'fecha', 'entrada', 'salida', )


@admin.register(Escala)
class Escala(admin.ModelAdmin):
    list_display = ('nombre', 'monto_hora', )

@admin.register(GrupoActividad)
class GrupoActividad(admin.ModelAdmin):
    list_display = ('nombre', )

admin.site.register(BloqueDePresencia)