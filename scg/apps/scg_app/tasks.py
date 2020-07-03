### built-in
import pythoncom
import win32com.client as wc
from subprocess import check_output
import datetime as dt
import os


DEFAULT_ROUTE = os.path.normpath(
    os.getcwd() + os.sep + os.pardir
    ) + '\\scg'

__ALLOWED_TASKS = {
    'sgc_nettime_sync': {
        '/sc': 'daily',                                     # scheduletype
        '/st': '00:00',                                     # starttime
        '/tr': DEFAULT_ROUTE + '\\scripts\\run_ntsync.vbs',   # taskrun
        '/ru': 'System',                                    # system user
    },
}

__TASKS_CONFIGS = {
    'sgc_nettime_sync': {
        'command_file': DEFAULT_ROUTE + '\\scripts\\ntsync_command.cmd',
        'command': 'python "{0}" pull_nettime >> "{1}" \nexit'.format(
            DEFAULT_ROUTE + '\\manage.py',
            DEFAULT_ROUTE + '\\scripts\\ntsync_history.log',
        )
    }
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


def create_commandfile(task_name):
    """ create a command and run file for a specific task """

    with open(__TASKS_CONFIGS.get(task_name).get('command_file'), 'w') as cf:
        cf.write(__TASKS_CONFIGS.get(task_name).get('command'))
        cf.close()

    with open(__ALLOWED_TASKS.get(task_name).get('/tr'), 'w') as rf:

        lines = [
            'Set oShell = CreateObject ("Wscript.Shell")\n',
            'Dim strArgs\n',
            'strArgs = "cmd /c {0}"\n'.format(
                __TASKS_CONFIGS.get(task_name).get('command_file')
            ),
            'oShell.Run strArgs, 0, false',
        ]

        rf.writelines(lines)
        rf.close()
    

def task_create(task_name):
    """ Create a task from recived parameters """
    
    #check if is allowed
    if task_name not in __ALLOWED_TASKS:
        return False

    #check if not exist
    if task_get_data(task_name):
        return False

    try:
        create_commandfile(task_name)
    except:
        return False

    options = {
        'schtasks': '/create',  # create command
        '/tn': task_name,       # taskname
    }
    options.update(__ALLOWED_TASKS.get(task_name))

    ### create task ###
    to_list = list()
    [to_list.extend([k, v]) for k, v in options.items()]
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
    """ for test only """
    
    TASK_NAME = 'sgc_nettime_sync'
    task_data = task_get_data(TASK_NAME)
    if not task_data: 
        try:
            task_create(TASK_NAME)
            task_data = task_get_data(TASK_NAME)
        except Exception as error:
            print(f'{error}')

    print(task_data)










