from django.core.management.base import BaseCommand, CommandError
from scg_app.models import Empleado, Sede, MotivoAusencia, Marcaje

class Command(BaseCommand):
    help = 'Import employees from netTime'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)

        #     poll.opened = False
        #     poll.save()

        try:
            Sede.update_from_nettime()
            MotivoAusencia.update_from_nettime()
            Empleado.update_from_nettime()
            Marcaje.update_from_nettime()

            #if everything was correctly ended
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported from netTime'
                )
            )

        except Exception as error:
            self.stdout.write(self.style.ERROR(f'{error}'))
