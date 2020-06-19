from django_extensions.management.jobs import DailyJob


class Job(DailyJob):
    help = "NT Sync."

    def execute(self):
        # executing empty sample job
        # passSede.update_from_nettime()
        # MotivoAusencia.update_from_nettime()
        # Empleado.update_from_nettime()
        # Marcaje.update_from_nettime()

        pass
