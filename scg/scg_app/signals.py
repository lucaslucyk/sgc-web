import datetime 

from django.db.models.signals import post_save
from django.dispatch import receiver

from scg_app.models import Clase

@receiver(post_save, sender=Clase)
def time_updates(sender, instance, **kwargs):
    hf = datetime.datetime.combine(instance.fecha, instance.horario_hasta)
    hi = datetime.datetime.combine(instance.fecha, instance.horario_desde)
    instance.horas = round((hf - hi).total_seconds() / 3600, 2)

    instance.save()
