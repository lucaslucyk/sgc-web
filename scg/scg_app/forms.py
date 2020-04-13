import datetime as dt
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone as tz
from .models import *

from django_select2.forms import Select2MultipleWidget
from dal import autocomplete

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

    dia_semana = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=settings.DIA_SEMANA_CHOICES, required=True, initial=None)
    dia_semana.widget.attrs.update({'class':'form-check-input'})

    # class Meta:
    #     model = Recurrencia
    #     fields = ('empleado')


class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=150, help_text="Obligatorio. Longitud máxima de 150 caracteres. Solo puede estar formado por letras, números y los caracteres @/./+/-/_.")
    email = forms.EmailField(max_length=200, help_text="Obligatorio. Longitud máxima de 200 caracteres. Formato valido: 'usuario@servidor.dominio'")

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

    empleado = forms.CharField(max_length=50, help_text="", required=False, widget=widget_search)
    empleado.widget.attrs.update({'placeholder': "Algún dato del empleado asignado...",})

    reemplazo = forms.CharField(max_length=50, help_text="", required=False, widget=widget_search)
    reemplazo.widget.attrs.update({'placeholder': "Algún dato del reemplazo...",})

    actividad = forms.CharField(max_length=50, help_text="", required=False, widget=widget_search)
    actividad.widget.attrs.update({'placeholder': "Algún dato de la actividad o grupo...",})

    dia_inicio = forms.CharField(max_length=10, help_text="", required=False, widget=widget_date)
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
        queryset=MotivoAusencia.objects.all(), 
        required=False, label="Motivo de ausencia", 
        empty_label="Todos"
    )
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.all(), 
        required=False, label="Sede", 
        empty_label="Todas"
    )

    solo_ausencia = forms.BooleanField(required=False, label="Solo ausencias", initial=False)
    solo_ausencia.widget.attrs.update({'class': 'form-check-input'})

    solo_reemplazos = forms.BooleanField(required=False, label="Solo reemplazos", initial=False)
    solo_reemplazos.widget.attrs.update({'class': 'form-check-input'})

    solo_confirmadas = forms.BooleanField(required=False, label="Solo confirmadas", initial=False)
    solo_confirmadas.widget.attrs.update({'class': 'form-check-input'})

class MarcajeForm(forms.Form):
    hora_marcaje = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), required=False, help_text="")
    hora_marcaje.widget.attrs.update({
        'class': 'form-control hour-input',
        'placeholder': "00:00",
        'aria-label': 'hora_marcaje',
        'aria-describedby': 'basic-addon1',
        })

class ReemplazoForm(forms.Form):
    reemplazo = forms.ModelChoiceField(
        queryset=Empleado.objects.all(), 
        required=False, 
        empty_label="Ninguno", 
        label="Reemplazante",
        )
    reemplazo.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Clase
        fields = ("reemplazo")

class MotivoAusenciaForm(forms.Form):
    motivo = forms.ModelChoiceField(
        queryset=MotivoAusencia.objects.all(), 
        required=False, 
        empty_label="Ninguno", 
        label="Motivo de Ausencia",
        )
    motivo.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = MotivoAusencia
        fields = ("id", "nombre")