### own
from scg_app.models import *

### django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from dynamic_raw_id.admin import DynamicRawIDMixin

### user extend ###
UserAdmin.fieldsets += (
    ('Perfil', {
        #'classes': ('collapse',),
        'fields': ('sedes', ),
    }),
)
UserAdmin.autocomplete_fields += ('sedes',)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    fields = (
        'id_netTime', 'apellido', 'nombre', 'dni', 'legajo', 'empresa',
        'escala', 'tipo', 'liquidacion')
    list_display = (
        'dni', 'apellido', 'nombre', 'legajo', 'empresa', 'id_netTime', 'tipo',
        'liquidacion',
    )
    autocomplete_fields = ('escala', )
    ordering = ('apellido', )
    
    #readonly_fields = ('apellido', 'nombre', 'dni', 'legajo', 'empresa', )
    # def has_delete_permission(self, request, obj=None):
    #     return True
    # def has_add_permission(self, request, obj=None):
    #    return False

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'codigo' )
    readonly_fields = ('nombre', 'tipo', 'id' )
    search_fields = ['nombre', 'codigo']
    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_add_permission(self, request, obj=None):
    #     return False

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo', )#'categoria', )

@admin.register(MotivoAusencia)
class MotivoAusenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'genera_pago', 'requiere_certificado')

@admin.register(Saldo)
class SaldoAdmin(admin.ModelAdmin):
    list_display = (
        'actividad', 'sede', 'desde', 'hasta', 'saldo_asignado',
        'saldo_disponible')

@admin.register(Recurrencia)
class RecurrenciaAdmin(admin.ModelAdmin):
    fields = (
        ('fecha_desde', 'horario_desde'), ('fecha_hasta', 'horario_hasta'),
        'empleado', 'sede', 'actividad', 'weekdays', 'locked')
    list_display = (
        'id', 'empleado', 'fecha_desde', 'fecha_hasta',
        'horario_desde', 'horario_hasta', 'sede',
        'actividad', 'get_dias_str', 'locked')
    list_filter = ['empleado', 'sede', 'actividad', 'locked']


# class ComentariosInLine(admin.InlineModelAdmin):
#     model = GrupoComentario
#     ct_fk_field = "object_id"
#     ct_field = "content_object"
#     extra = 1
#     ordering = ("-fecha",)
#     #raw_id_fields = ("producto",)
#     #autocomplete_fields = ["comentario"]

@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    #inlines = [ComentariosInLine]
    fields = (
        'recurrencia', ('dia_semana', 'fecha'),
        ('horario_desde', 'horario_hasta'), 'actividad', 'sede', 'empleado',
        'modificada', 'estado', 'presencia', 'ausencia', 'reemplazo', 'horas',
        'confirmada', 'locked')

    list_display = (
        'estado', 'presencia', 'empleado', 'reemplazo', 'sede',
        'actividad', 'dia_semana', 'fecha', 'horario_desde', 'horario_hasta',
        'modificada', 'ausencia', 'confirmada', 'locked', 'horas')

    readonly_fields = (
        'recurrencia', 'creacion', 'dia_semana', 'fecha',
        'horario_desde', 'horario_hasta', 'actividad', 'sede', 'empleado',
        'modificada', 'presencia', 'ausencia', 'reemplazo', 'estado', 'horas')

    search_fields = [
        'empleado__nombre','empleado__apellido', 'empleado__dni',
        'empleado__legajo', 'empleado__empresa', 
        'reemplazo__nombre', 'reemplazo__apellido', 'reemplazo__dni',
        'reemplazo__legajo', 'reemplazo__empresa',
        'sede__nombre', 'ausencia__nombre', 'ausencia__grupo',
        'fecha', 'horas'
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

@admin.register(Marcaje)
class MarcajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'fecha', 'hora', 'usuario', 'locked')

@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto_hora', )
    search_fields = ['nombre', 'grupo__nombre']
    ordering = ('nombre', )

@admin.register(GrupoActividad)
class GrupoActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'tipo' )

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    autocomplete_fields = ('clases',)

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('desde', 'hasta', 'bloqueado')

    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(BloqueDePresencia)
class BloqueDePresenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha', 'inicio', 'fin')

    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'usuario', 'accion', '__str__', 'locked')


@admin.register(GrupoComentario)
class GrupoComentarioAdmin(admin.ModelAdmin):
    list_display = (
        'content_type', 'content_object', 'comentario')

#admin.site.register(BloqueDePresencia)
admin.site.register(TipoLiquidacion)
admin.site.register(TipoContrato)
