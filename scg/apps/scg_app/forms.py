# -*- coding: utf-8 -*-

### built-in ###
import datetime as dt

### third ###
#from django_select2.forms import Select2MultipleWidget
#from dal import autocomplete

### django ###
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone as tz

### own ###
from apps.scg_app.models import *

class PeriodoForm(forms.Form):
    widget_date = forms.TextInput(attrs={
        'type': 'date',
        'class': 'form-control',
        'placeholder': 'aaaa-mm-dd',
    })

    desde = forms.CharField(max_length=10, required=True, widget=widget_date)
    hasta = forms.CharField(max_length=10, required=True, widget=widget_date)

    bloqueado = forms.BooleanField(
        required=False, label="Bloqueado", initial=True)
    bloqueado.widget.attrs.update({
        'data-bootstrap-switch': '',
        'data-off-color': 'danger',
        'data-on-color': 'success',
    })

class PeriodoUpdForm(PeriodoForm, forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ['desde', 'hasta', 'bloqueado']

class SaldoForm(forms.Form):
    widget_date = forms.TextInput(attrs={
        'type': 'date',
        'class': 'form-control',
        'placeholder':'aaaa-mm-dd',
    })

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.all().order_by('nombre'), 
        required=True, label="Sede", 
        empty_label="Seleccione una sede..."
    )
    actividad = forms.ModelChoiceField(
        queryset=Actividad.objects.all().order_by('nombre'), 
        required=True, label="Sede", 
        empty_label="Seleccione una actividad..."
    )
    desde = forms.CharField(max_length=10, required=True, widget=widget_date)
    hasta = forms.CharField(max_length=10, required=True, widget=widget_date)

    saldo_asignado = forms.IntegerField(required=True)
    saldo_asignado.widget.attrs.update({
        'class':'form-control',
        'placeholder': '0',
        'min': '1',
        'max': '9999',
    })

class SaldoUpdForm(SaldoForm, forms.ModelForm):

    class Meta:
        model = Saldo
        fields = ['sede', 'actividad', 'desde', 'hasta', 'saldo_asignado']

class ClaseUpdForm(forms.ModelForm):
    """docstring for ClaseUpdForm"""

    horario_desde = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
        help_text="Horario de inicio de clase", required=True)#, initial="00:00")
    horario_desde.widget.attrs.update({'class': 'form-control hour-input', 'placeholder':'00:00'})
    horario_hasta = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
        help_text="Horario de fin de clase", required=True)#, initial="00:00")
    horario_hasta.widget.attrs.update({'class': 'form-control hour-input', 'placeholder':'00:00'})

    comentario = forms.CharField(widget=forms.Textarea, required=True)
    comentario.widget.attrs.update({
        'class': 'form-control',
        'rows': '3',
        'placeholder': 'Ingrese un comentario...',
    })

    class Meta:
        model = Clase
        fields = ['horario_desde', 'horario_hasta', 'comentario']

class RecurrenciaForm(forms.Form):
    #empleado = forms.ModelMultipleChoiceField(queryset=Empleado.objects.all(), widget=Select2MultipleWidget)
    widget_date = forms.TextInput(attrs={
        'type': 'date',
        'class': 'form-control',
        'placeholder':'aaaa-mm-dd',
    })
    
    fecha_desde = forms.CharField(max_length=10, help_text="", required=True, widget=widget_date)
    fecha_hasta = forms.CharField(max_length=10, help_text="", required=True, widget=widget_date)

    horario_desde = forms.TimeField(widget=forms.TimeInput(format="%H:%M"),
        help_text="Horario de inicio de clase", required=True)#, initial="00:00")
    horario_desde.widget.attrs.update({'class': 'form-control hour-input', 'placeholder':'00:00'})

    horario_hasta = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
        help_text="Horario de fin de clase", required=True)
    horario_hasta.widget.attrs.update({'class': 'form-control hour-input', 'placeholder':'23:59'})

    weekdays = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, 
        choices=settings.DIA_SEMANA_CHOICES, required=True, initial=None
    )
    weekdays.widget.attrs.update({'class':'form-check-input'})

    # class Meta:
    #     model = Recurrencia
    #     fields = ('empleado')

class RecurrenciaUpdForm(RecurrenciaForm, forms.ModelForm):

    class Meta:
        model = Recurrencia
        fields = ['fecha_desde', 'fecha_hasta', 
            'horario_desde', 'horario_hasta', 'weekdays',
        ]

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        max_length=50, 
        help_text="Obligatorio. 50 caracteres sin símbolos especiales."
    )
    email = forms.EmailField(
        max_length=200, 
        help_text="Obligatorio. 200 caracteres máximo."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class FiltroForm(forms.Form):
    widget_search = forms.TextInput(attrs={
        'type': 'search',
        'class': 'form-control py-2 border-right-0 border',
    })
    widget_date = forms.TextInput(attrs={
        'type': 'date',
        'class': 'form-control',
        'placeholder':'aaaa-mm-dd',
    })
    widget_time = forms.TextInput(attrs={
        'type': 'time',
        'class': 'form-control',
    })
    tri_state_check = {
        'min': '-1',
        'max': '1',
        'tri-state-check': '',
    } 

    empleado = forms.CharField(max_length=50, help_text="", required=False, widget=widget_search)
    empleado.widget.attrs.update({'placeholder': "Algún dato del empleado asignado...",})

    reemplazo = forms.CharField(max_length=50, help_text="", required=False, widget=widget_search)
    reemplazo.widget.attrs.update({'placeholder': "Algún dato del reemplazo...",})

    actividad = forms.CharField(max_length=50, help_text="", required=False, widget=widget_search)
    actividad.widget.attrs.update({'placeholder': "Algún dato de la actividad o grupo...",})

    dia_inicio = forms.CharField(max_length=10, initial=datetime.date.today().strftime("%Y-%m-%d"),
        required=False, widget=widget_date)
    dia_fin = forms.CharField(max_length=10, help_text="", required=False, widget=widget_date)

    hora_inicio = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
        initial="00:00", help_text="Horario de inicio de clase")
    hora_inicio.widget.attrs.update({'class': 'form-control  hour-input', 'placeholder':'00:00'})

    hora_fin = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
        initial="23:59", help_text="Horario de fin de clase")
    hora_fin.widget.attrs.update({'class': 'form-control  hour-input', 'placeholder':'23:59'})

    dia_semana = forms.ChoiceField(
        widget=forms.Select, 
        choices=(('', 'Todos'), *settings.DIA_SEMANA_CHOICES), 
        required=False, label="Día de semana", initial=None,
    )
    estado = forms.ChoiceField(
        widget=forms.Select, 
        choices=(('', 'Todos'), *settings.ESTADOS_CHOICES), 
        required=False, label="Estado", initial=None,
    )
    motivo_ausencia = forms.ModelChoiceField(
        queryset=MotivoAusencia.objects.all().order_by("nombre"), 
        required=False, label="Motivo de ausencia", 
        empty_label="Todos"
    )
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.all().order_by("nombre"),
        required=False, label="Sede", 
        empty_label="Todas"
    )
    
    solo_ausencia = forms.IntegerField(required=False)
    solo_ausencia.widget.attrs.update(tri_state_check)

    solo_reemplazos = forms.IntegerField(required=False)
    solo_reemplazos.widget.attrs.update(tri_state_check)

    solo_confirmadas = forms.IntegerField(required=False)
    solo_confirmadas.widget.attrs.update(tri_state_check)

    solo_bloqueadas = forms.IntegerField(required=False)
    solo_bloqueadas.widget.attrs.update(tri_state_check)

class MarcajeForm(forms.Form):
    hora_marcaje = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), required=False, help_text="")
    hora_marcaje.widget.attrs.update({
        'class': 'form-control hour-input',
        'placeholder': "00:00",
        'aria-label': 'hora_marcaje',
        'aria-describedby': 'basic-addon1',
        })

class MotivoAusenciaForm(forms.Form):
    motivo = forms.ModelChoiceField(
        queryset=MotivoAusencia.objects.all().order_by("nombre"), 
        required=False, 
        empty_label="Ninguno", 
        label="Motivo de Ausencia",
        )
    motivo.widget.attrs.update({'class': 'form-control custom-select'})

    #adjunto = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    adjunto = forms.FileField(required=False)
    adjunto.widget.attrs.update({'class':'custom-file-input', 'id':'adjunto'})

    comentario = forms.CharField(widget=forms.Textarea, required=False)
    comentario.widget.attrs.update({
        'class': 'form-control',
        'rows': '2',
        'placeholder': 'Ingrese un comentario...',
    })

    class Meta:
        model = MotivoAusencia
        fields = ("id", "nombre")

class ComentarioForm(forms.Form):
    comentario = forms.CharField(widget=forms.Textarea, required=False)
    comentario.widget.attrs.update({
        'class': 'form-control',
        'rows': '2',
        'placeholder': 'Ingrese un comentario...',
    })
