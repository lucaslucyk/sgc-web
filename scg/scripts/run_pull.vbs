Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "cmd /c pull_nettime.cmd"
oShell.Run strArgs, 0, false