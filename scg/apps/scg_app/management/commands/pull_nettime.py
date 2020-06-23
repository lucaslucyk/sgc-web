# -*- coding: utf-8 -*-

### built-in ###
from datetime import datetime

### third ###
#...

### django ###
from django.core.management.base import BaseCommand, CommandError

### own ###
from apps.scg_app.models import Empleado, Sede, MotivoAusencia, Marcaje

class Command(BaseCommand):
    help = 'Import data from netTime'

    def handle(self, *args, **options):
        try:
            #inform what start the import
            self.stdout.write(
                f'{datetime.now()} - INFO - Starting import from netTime...'
            )

            Sede.update_from_nettime()
            MotivoAusencia.update_from_nettime()
            Empleado.update_from_nettime()
            Marcaje.update_from_nettime()

            #if everything was correctly ended
            self.stdout.write(
                self.style.SUCCESS(
                    f'{datetime.now()} - OK - Successfully imported from netTime!'
                )
            )

        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'{datetime.now()} - ERROR - {error}'
                )
            )
