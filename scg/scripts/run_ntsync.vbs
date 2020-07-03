Set oShell = CreateObject ("Wscript.Shell")
Dim strArgs
strArgs = "cmd /c C:\Users\LucasLucyk\Documents\Programming\Python\spec\sgc-web\scg\scripts\ntsync_command.cmd"
oShell.Run strArgs, 0, false