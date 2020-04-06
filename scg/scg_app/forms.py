import datetime as dt
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone as tz
from .models import *

class SignUpForm(UserCreationForm):
	username = forms.CharField(max_length=150, help_text="Obligatorio. Longitud máxima de 150 caracteres. Solo puede estar formado por letras, números y los caracteres @/./+/-/_.")
	email = forms.EmailField(max_length=200, help_text="Obligatorio. Longitud máxima de 200 caracteres. Formato valido: 'usuario@servidor.dominio'")

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

class ProgRecurrenciaForm(forms.Form):
	dia_semana = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=settings.DIA_SEMANA_CHOICES, required=True, initial=None)
	fecha_desde = forms.DateField(widget=forms.SelectDateWidget(years=range(2010, 2040)), initial=tz.now(), help_text="Fecha inicio del periodo")
	fecha_hasta = forms.DateField(widget=forms.SelectDateWidget(years=range(2010, 2040)), initial=tz.now() + dt.timedelta(days=1), help_text="Fecha final del periodo")
	horario_desde = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), help_text="Horario de inicio de clase", initial=(tz.now() - dt.timedelta(hours=3)).replace(minute=0))
	horario_hasta = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), help_text="Horario de finalizacion de clase", initial=(tz.now() - dt.timedelta(hours=2)).replace(minute=0))
	actividad = forms.ModelChoiceField(queryset=Actividad.objects.all())
	empleado = forms.ModelChoiceField(queryset=Empleado.objects.all())
	sede = forms.ModelChoiceField(queryset=Sede.objects.all())

	class Meta:
		model = Clase
		fields = ("dia_semana", "fecha_desde", "fecha_hasta", "horario_desde", "horario_hasta", "actividad", "empleado", "sede")

class FiltroForm(forms.Form):
	widget_search = forms.TextInput(attrs={
		'type': 'search',
		'class': 'form-control py-2 border-right-0 border',
	})
	widget_date = forms.TextInput(attrs={
		'type': 'date',
		'class': 'form-control',
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
		help_text="Horario de inicio de clase", initial="00:00")
	hora_inicio.widget.attrs.update({'class': 'form-control'})

	hora_fin = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
		help_text="Horario de fin de clase", initial="23:59")
	hora_fin.widget.attrs.update({'class': 'form-control'})

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
	hora_marcaje = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), 
		help_text="", initial="00:00")
	hora_marcaje.widget.attrs.update({
		'class': 'form-control',
		'placeholder': "00:00",
		'aria-label': 'hora_marcaje',
		'aria-describedby': 'basic-addon1',
		})

class ReemplazoForm(forms.Form):
	reemplazo = forms.ModelChoiceField(
		queryset=Empleado.objects.all(), 
		required=True, 
		empty_label="Seleccione un empleado", 
		label="Reemplazante",
		)
	reemplazo.widget.attrs.update({'class': 'form-control'})

	class Meta:
		model = Clase
		fields = ("reemplazo")

class MotivoAusenciaForm(forms.Form):
	motivo = forms.ModelChoiceField(
		queryset=MotivoAusencia.objects.all(), 
		required=True, 
		empty_label="Seleccione un motivo", 
		label="Motivo de Ausencia",
		)
	motivo.widget.attrs.update({'class': 'form-control'})

	class Meta:
		model = MotivoAusencia
		fields = ("id", "nombre")