Option Explicit
Dim shell, fso, root, python
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
python = root & "\runtime\python\pythonw.exe"
If Not fso.FileExists(python) Then python = root & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(python) Then WScript.Quit 1
shell.Run """" & python & """ """ & root & "\launcher.py"" stop", 0, False
