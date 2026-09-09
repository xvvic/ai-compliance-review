Option Explicit
Dim shell, fso, root, python
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
python = root & "\runtime\python\pythonw.exe"
If Not fso.FileExists(python) Then python = root & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(python) Then
  MsgBox "Runtime missing. Please extract the complete portable package.", 48, "AI Compliance Review"
  WScript.Quit 1
End If
shell.Run """" & python & """ """ & root & "\launcher.py"" start", 0, False
