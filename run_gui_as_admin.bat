@echo off

:: Delete old logs
if exist dns_switcher_gui.log del dns_switcher_gui.log
if exist dns_switcher_gui.err del dns_switcher_gui.err

:: Run the application as administrator with log redirection
powershell -Command "Start-Process -FilePath 'dist\dns_switcher_gui.exe' -ArgumentList '/log=dns_switcher_gui.log', '/err=dns_switcher_gui.err' -Verb RunAs"

:: Wait for the process to start and check if it's running
timeout /t 2 >nul

echo DNS Switcher GUI has been started as administrator.
echo Logs are being written to dns_switcher_gui.log and dns_switcher_gui.err.
pause