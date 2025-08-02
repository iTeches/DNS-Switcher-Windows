@echo off
REM Simple launcher for DNS Switcher

:menu
cls
echo ====================================
echo         DNS Switcher Launcher
 echo ====================================
echo 1. Run Command Line Version
echo 2. Run GUI Version
echo 3. Exit
 echo ====================================
set /p choice=Enter your choice (1-3): 

if %choice% == 1 goto commandline
if %choice% == 2 goto gui
if %choice% == 3 goto exit

echo Invalid choice. Please try again.
pause
goto menu

:commandline
echo Starting Command Line Version...
dist\dns_switcher.exe
pause
goto menu

:gui
echo Starting GUI Version...
dist\dns_switcher_gui.exe
pause
goto menu

:exit
echo Exiting...
pause