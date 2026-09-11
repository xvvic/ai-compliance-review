Option Explicit
Dim shell, fso, root, python
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
' 用 python.exe(控制台子系统,窗口隐藏)而非 pythonw.exe:
' claude.exe 在完全无控制台的进程链下会报 0x0000142(DLL 初始化失败),
' 隐藏的控制台足以让它正常启动,用户体验不变。
python = root & "\runtime\python\python.exe"
If Not fso.FileExists(python) Then python = root & "\.venv\Scripts\python.exe"
If Not fso.FileExists(python) Then
  MsgBox "Runtime missing. Please extract the complete portable package.", 48, "AI Compliance Review"
  WScript.Quit 1
End If
shell.Run """" & python & """ """ & root & "\launcher.py"" start", 0, False
