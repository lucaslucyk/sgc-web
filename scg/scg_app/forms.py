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

class FiltrosForm(forms.Form):
	estado = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=settings.ESTADOS_CHOICES, required=False, label="Estado de la Clase", initial=None)
	empleado_asignado = forms.ModelChoiceField(queryset=Empleado.objects.all(), required=False, label="Asignado", empty_label="---")
	empleado_ejecutor = forms.ModelChoiceField(queryset=Empleado.objects.all(), required=False, label="Realizador", empty_label="---")
	actividad = forms.ModelChoiceField(queryset=Actividad.objects.all(), required=False, empty_label="---")
	fecha_desde = forms.DateField(widget=forms.SelectDateWidget(years=range(2010, 2040)), label="Desde", initial=None, required=False)
	fecha_hasta = forms.DateField(widget=forms.SelectDateWidget(years=range(2010, 2040)), label="Hasta", initial=None, required=False)
	dias = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=settings.DIA_SEMANA_CHOICES, required=False,)
	horario_desde = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), help_text="Horario de inicio de clase", initial=dt.time(0, 0), required=False)
	horario_hasta = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), help_text="Horario de finalizacion de clase", initial=dt.time(0, 0), required=False)
	clases_ausentes = forms.BooleanField(required=False, label="Mostrar solo Ausencias", initial=False)
	clases_reemplazos = forms.BooleanField(required=False, label="Mostrar solo Reemplazos", initial=False)

	class Meta:
		model = Clase
		fields = ("fecha_desde", "fecha_hasta", "horario_desde", "horario_hasta", "actividad", "empleado", )

class MarcajeForm(forms.Form):
	nuevo_marcaje = forms.TimeField(widget=forms.TimeInput(format="%H:%M"), help_text="Horario del marcaje a agregar", initial=dt.time(0, 0), required=True)

	class Meta:
		model = Marcaje
		fields = ("nuevo_marcaje")

class ReemplazoForm(forms.Form):
	reemplazo = forms.ModelChoiceField(queryset=Empleado.objects.all(), required=False, label="Reemplazante")

	class Meta:
		model = Clase
		fields = ("reemplazo")

class AusenciaForm(forms.Form):
	motivo = forms.CharField(widget=forms.Textarea, required=True, label="Motivo, Razon o Circunstancia de la Ausencia")

	class Meta:
		model = Clase
		fields = ()
