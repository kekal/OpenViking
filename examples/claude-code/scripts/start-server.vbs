' start-server.vbs — Launch OpenViking server as a hidden background process (Windows)
' Used by up.bat to avoid a visible terminal window.
Set WshShell = CreateObject("WScript.Shell")
WshShell.Environment("Process")("OPENVIKING_CONFIG_FILE") = WshShell.ExpandEnvironmentStrings("%USERPROFILE%\.openviking\ov.conf")
WshShell.Run "cmd /c openviking-server --config """ & WshShell.ExpandEnvironmentStrings("%USERPROFILE%\.openviking\ov.conf") & """ --port 1933 > """ & WshShell.ExpandEnvironmentStrings("%USERPROFILE%\.openviking\server.log") & """ 2>&1", 0, False
