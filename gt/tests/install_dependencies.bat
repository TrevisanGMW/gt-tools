@echo off
@title =  Unittest Dependency Installer
setlocal enabledelayedexpansion

set "launch_args=%1"
set "preferred_version=2027"
set "path_bat_script=%~dp0"
set "path_autodesk=C:\Program Files\Autodesk"
set "path_mayapy_end=\bin\mayapy.exe"
set "installation_status="


:LAUNCH
echo %preferred_version%| findstr /R "[0-9][0-9][0-9][0-9]$" > nul
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
	goto TIMED_EXIT
    ) else (
	@echo Installing MayaPy Dependencies...	
	"%path_mayapy%" -m pip install numpy
	"%path_mayapy%" -m pip install scipy
	@echo.	
	pause
    )
endlocal
goto EOF

:PAUSE
pause

:TIMED_EXIT
timeout /t 2 /nobreak

:EOF
exit /s