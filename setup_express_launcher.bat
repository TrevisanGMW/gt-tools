@echo off
@title =  Command-line Package Installer
setlocal enabledelayedexpansion

set "launch_args=%1"
set "preferred_version=%2"
set "path_bat_script=%~dp0"
set "path_package_init=!path_bat_script!\setup_drag_drop_maya.py"
set "path_autodesk=C:\Program Files\Autodesk"
set "path_mayapy_end=\bin\mayapy.exe"
set "installation_status="

:ARGS
if "%1"=="" (
	goto MENU
) else (
	set "launch_args=%*"
	goto LAUNCH
)

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
IF %M%==1 GOTO SET_ARGS_GUI
IF %M%==2 GOTO SET_ARGS_INSTALL
IF %M%==3 GOTO SET_ARGS_UNINSTALL
IF %M%==4 GOTO SET_ARGS_LAUNCH
IF %M%==5 GOTO ABOUT
GOTO EOF

:SET_ARGS_GUI
set "launch_args=-install -gui"
GOTO LAUNCH

:SET_ARGS_INSTALL
set "launch_args=-install -clean"
GOTO LAUNCH

:SET_ARGS_UNINSTALL
set "launch_args=-uninstall"
GOTO LAUNCH

:SET_ARGS_LAUNCH
set "launch_args=-launch"
GOTO LAUNCH

:LAUNCH
echo %preferred_version%| findstr /R "^-[0-9][0-9][0-9][0-9]$" > nul
if errorlevel 1 (
    goto GET_LATEST_MAYAPY
) else (
    goto GET_PREFERRED_MAYAPY
)

:GET_PREFERRED_MAYAPY
set "preferred_version_no_dash="
for /f "tokens=*" %%a in ('echo !preferred_version!') do (
	set "line=%%a"
	set "line=!line:-=!"
	set "preferred_version_no_dash=!preferred_version_no_dash!!line!"
)
if exist "%path_autodesk%\Maya%preferred_version_no_dash%%path_mayapy_end%" (
	set "path_mayapy=%path_autodesk%\Maya%preferred_version_no_dash%%path_mayapy_end%"
	GOTO CHECK_MAYAPY_EXISTENCE
) else (
    echo "Unable to find preferred version: %preferred_version_no_dash%. Looking for other versions..."
	timeout /t 2 /nobreak
	GOTO GET_LATEST_MAYAPY
)

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
	GOTO TIMED_EXIT
    ) else (
	"%path_mayapy%" "%path_package_init%" %launch_args%
    )
endlocal
GOTO TIMED_EXIT

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

:TIMED_EXIT
timeout /t 3 /nobreak

:EOF
EXIT
