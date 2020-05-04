import pythoncom
import win32com.client as wc
from subprocess import check_output
import datetime as dt

DEFAULT_ROUTE = r'"C:\Users\LucasLucyk\Documents\Programming\Python\spec\sgc-web\scg\scripts\run_pull.vbs"'
__ALLOWED_TASKS = {
    'sgc_nettime_sync': {
        '/sc': 'daily',         # scheduletype
        '/st': '00:00',         # starttime
        '/tr': DEFAULT_ROUTE,   # taskrun
        '/ru': 'System',        # system user
    },
}

STATES = {
    0: 'Unknown',
    1: 'Disabled',
    2: 'Queued',
    3: 'Ready',
    4: 'Running'
}

def task_get_data(task_name):
    """ Get all system tasks and return data of a specific recived """

    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return {}

    task_data = {}
    pythoncom.CoInitialize()

    ### get tasks ###
    scheduler = wc.Dispatch('Schedule.Service')
    scheduler.Connect()
    folders = [scheduler.GetFolder('\\')]
    for folder in folders:
        for task in folder.GetTasks(0):
            #format --> "\name"
            if task_name == task.Path.lstrip('\\'):
                task_data["Path"] = task.Path
                task_data["State"] = STATES.get(task.State)
                task_data["LastRunTime"] = dt.datetime.strptime(
                    str(task.LastRunTime).replace("+00:00", ""),
                    '%Y-%m-%d %H:%M:%S'
                )
    
    return task_data


def task_create(task_name, sc='daily', st='00:00', tr=DEFAULT_ROUTE, ru='System'):
    """ Create a task from recived parameters """
    
    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if task_get_data(task_name):
        return False

    OPTIONS = {
        'schtasks': '/create',  # create command
        '/tn': task_name,       # taskname
    }
    OPTIONS.update(__ALLOWED_TASKS.get(task_name))

    ### create task ###
    to_list = list()
    [to_list.extend([k, v]) for k, v in OPTIONS.items()]
    command = r' '.join(to_list)

    #command execute
    check_output(command, shell=True)

def task_run(task_name):
    """ Execute a specific recived task """

    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if not task_get_data(task_name):
        return False

    command = f'schtasks /run /tn {task_name}'
    
    #command execute
    check_output(command, shell=True)

def task_stop(task_name):
    """ Stops a program started by a task """

    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if not task_get_data(task_name):
        return False

    command = f'schtasks /end /tn {task_name}'

    #command execute
    check_output(command, shell=True)

def task_enable(task_name):
    """ Enable a specific task """

    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if not task_get_data(task_name):
        return False

    command = f'schtasks /change /tn {task_name} /ENABLE'

    #command execute
    check_output(command, shell=True)


def task_disable(task_name):
    """ Disable a specific task """

    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if not task_get_data(task_name):
        return False

    command = f'schtasks /change /tn {task_name} /DISABLE'

    #command execute
    check_output(command, shell=True)

def task_delete(task_name):
    """ Deletes a specific scheduled task """

    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if not task_get_data(task_name):
        return False

    command = f'schtasks /delete /tn {task_name} /f'

    #command execute
    check_output(command, shell=True)


if __name__ == "__main__":

    #TASK_NAME = 'sgc_pull_nettime'
    TASK_NAME = 'pull_from_nettime'
    task_data = task_get_data(TASK_NAME)
    if not task_data: 
        try:
            task_create(TASK_NAME, sc='daily', st='00:00', tr=DEFAULT_ROUTE, ru='System')
            task_data = task_get_data(TASK_NAME)
        except Exception as error:
            print(f'{error}')

    print(task_data)










