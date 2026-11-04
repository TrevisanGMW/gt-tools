@echo off
setlocal
rem Opens the Batch Processor outside of Maya. Drag a .batch file onto this bat to open that project.
set "SCRIPT=%~dp0standalone_main.py"
set "MAYAPY="
if defined MAYAPY_PATH if exist "%MAYAPY_PATH%" set "MAYAPY=%MAYAPY_PATH%"
if not defined MAYAPY for %%V in (2025 2026 2024 2023) do if not defined MAYAPY if exist "%ProgramFiles%\Autodesk\Maya%%V\bin\mayapy.exe" set "MAYAPY=%ProgramFiles%\Autodesk\Maya%%V\bin\mayapy.exe"
if not defined MAYAPY (
    echo mayapy.exe was not found. Set the MAYAPY_PATH environment variable to your mayapy.exe path.
    pause
    exit /b 1
)
if "%~1"=="" (
    start "" /min "%MAYAPY%" "%SCRIPT%" --hide-console
) else (
    start "" /min "%MAYAPY%" "%SCRIPT%" --hide-console --project-file "%~1"
)
endlocal
