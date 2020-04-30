import win32com.client as wc
from subprocess import check_output

### get tasks ###
"""
STATES = {
  0: 'Unknown',
  1: 'Disabled',
  2: 'Queued',
  3: 'Ready',
  4: 'Running'
}

scheduler = wc.Dispatch('Schedule.Service')
scheduler.Connect()
folders = [scheduler.GetFolder('\\')]
for folder in folders:
    for task in folder.GetTasks(0):
            print(task.Path, STATES.get(task.State), task.LastRunTime)

            #format --> "\name"
"""

### create task ###
ROUTE = r'"C:\Users\LucasLucyk\Documents\Programming\Python\spec\sgc-web\scg\scripts\run_pull.vbs"'
OPTIONS = {
  'schtasks': '/create',      #create command

  '/tn': 'sgc_pull_nettime',  #taskname
  '/sc': 'daily',             #scheduletype
  '/st': '00:00',             #starttime
  '/tr': ROUTE,               #taskrun
  '/ru': 'System',            #system user

  # '/ed': '31/12/2002' #enddate
}

to_list = list()
[to_list.extend([k, v]) for k, v in OPTIONS.items()]

command = r' '.join(to_list)
print(command)

#create task
check_output(command, shell=True)
