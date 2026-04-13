Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batchPath = scriptDir & "\bin\open-local-web.bat"
cmd = """" & batchPath & """"

For Each arg In WScript.Arguments
  cmd = cmd & " """ & Replace(arg, """", """""") & """"
Next

shell.Run cmd, 0, False
