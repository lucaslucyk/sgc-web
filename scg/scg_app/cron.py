from scg_app.models import Empleado

def pull_synchronous():
    """ all netTime pulls in corresponding order """

    try:
        Empleado.update_from_nettime()
    except Exception as error:
        print(error)
