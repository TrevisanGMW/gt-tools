@echo off
@title =  Command-line Package Installer
setlocal enabledelayedexpansion

set launch_option="%1"
set "path_bat_script=%~dp0"
set "path_package_init=!path_bat_script!__init__.py"
set "path_autodesk=C:\Program Files\Autodesk"
set "path_mayapy_end=\bin\mayapy.exe"
set "installation_status="

if %launch_option%=="-test" goto TEST

:MENU
@echo off
cls
color 0A
@echo on
@echo.
@echo.
@echo        лллллл лллллллл     лллллллл  лллллл   лллллл  лл      ллллллл 
@echo       лл         лл           лл    лл    лл лл    лл лл      лл      
@echo       лл   ллл   лл           лл    лл    лл лл    лл лл      ллллллл 
@echo       лл    лл   лл           лл    лл    лл лл    лл лл           лл 
@echo        лллллл    лл           лл     лллллл   лллллл  ллллллл ллллллл    
@echo.
@echo.
@echo                   ллллллл ллллллл лллллллл лл    лл лллллл  
@echo                   лл      лл         лл    лл    лл лл   лл 
@echo                   ллллллл ллллл      лл    лл    лл лллллл  
@echo                        лл лл         лл    лл    лл лл      
@echo                   ллллллл ллллллл    лл     лллллл  лл   
@echo.
@echo.
@echo.
@echo. 	1 = Initialize GUI Installer
@echo. 	2 = Perform Express Install
@echo. 	3 = Perform Express Uninstall
@echo. 	4 = Launch Without Installing
@echo. 	5 = About / Help
@echo.
@echo.
@echo off
SET /P M=Type 1, 2, 3, 4 or 5 then press ENTER:
IF %M%==1 GOTO GUI
IF %M%==2 GOTO INSTALL
IF %M%==3 GOTO UNINSTALL
IF %M%==4 GOTO LAUNCH
IF %M%==5 GOTO ABOUT
GOTO EOF

:GUI
set "launch_option=-install -gui"
GOTO GET_LATEST_MAYAPY

:INSTALL
set "launch_option=-install -clean"
GOTO GET_LATEST_MAYAPY

:UNINSTALL
set "launch_option=-uninstall"
GOTO GET_LATEST_MAYAPY

:LAUNCH
set "launch_option=-launch"
GOTO GET_LATEST_MAYAPY

:LAUNCH_DEV
set "launch_option=-launch -dev"
GOTO GET_LATEST_MAYAPY

:TEST
set "launch_option=-test %2 %3"
GOTO GET_LATEST_MAYAPY

:GET_LATEST_MAYAPY
set "latest_folder="
for /d %%G in ("%path_autodesk%\*") do (
    set "folder_name=%%~nG"
    if "!folder_name!" equ "" set "folder_name=%%~xG"
    echo !folder_name! | findstr /r "^Maya[0-9][0-9][0-9][0-9]" > nul && set "latest_folder=%%G"
)
set "path_mayapy=%latest_folder%%path_mayapy_end%"

:CHECK_MAYAPY_EXISTENCE
if not exist "%path_mayapy%" (
	set "installation_status=Unable to detect Maya installation"
	GOTO END
    ) else (
	"%path_mayapy%" %path_package_init% %launch_option%
    )
endlocal
GOTO PAUSE


:ABOUT
@echo off
color 02
cls
endlocal
@echo on
@echo.
@echo.               _
@echo.              ( )                GT-Tools Package Setup
@echo.               H                  
@echo.               H                 This batch file attempts to install the package without
@echo.              _H_                opening Maya or using the drag and drop python script.
@echo.           .-'-.-'-.
@echo.          /         \            The installation process copies the necessary files to
@echo.         !           !           the maya settings folder. Usually: "Documents\maya\gt-tools".
@echo.         !   .-------'._         
@echo.         !  / /  '.' '. \        The installation will also add an initialization line to every 
@echo.         !  \ \ @   @ / /        "userSetup.mel" file found the maya the preference folder.
@echo.         !   '---------'         (This process will not affect existing lines)
@echo.         !    _______!           
@echo.         !  .'-+-+-+!            Options:
@echo.         !  '.-+-+-+!            1. Initialize GUI Installer: Open full installer GUI (Same as in Maya)
@echo.         !    """""" !           2. Perform Express Install: Install package through the command-line
@echo.         '-._______.-'           3. Perform Express Uninstall: Uninstall through the command-line
@echo.                                 4. Launch Without Installing: Run package from current location
@echo.
@echo. 
@echo. 
@echo off
pause
setlocal enabledelayedexpansion
GOTO MENU

:PAUSE
pause

:EOF
EXIT