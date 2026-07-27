@echo off
@title = Unittest Dependency Installer
setlocal enabledelayedexpansion

set "path_autodesk=C:\Program Files\Autodesk"
set "path_mayapy_end=\bin\mayapy.exe"
set "maya_found=0"

:: Define dependencies here, separated by spaces
set "dependencies=numpy scipy"

echo Searching for Maya installations in "%path_autodesk%"...

:: Iterate over all folders in the Autodesk directory starting with "Maya"
for /d %%G in ("%path_autodesk%\Maya*") do (
    set "folder_name=%%~nG"
    
    :: Verify the folder matches the Maya + 4-digit year pattern
    echo !folder_name! | findstr /r "^Maya[0-9][0-9][0-9][0-9]" > nul
    if not errorlevel 1 (
        set "path_mayapy=%%G%path_mayapy_end%"
        
        :: Check if mayapy.exe actually exists in this version's bin folder
        if exist "!path_mayapy!" (
            set "maya_found=1"
            echo.
            echo =======================================================
            echo Found: !folder_name!
            echo Installing dependencies...
            echo =======================================================
            
            :: Iterate through the dependency list and install each one
            for %%D in (%dependencies%) do (
                echo.
                echo --- Installing %%D ---
                "!path_mayapy!" -m pip install %%D
            )
        )
    )
)

:: Check if at least one installation was found and processed
if "!maya_found!"=="0" (
    echo.
    echo Unable to detect any Maya installations with mayapy.exe.
    goto TIMED_EXIT
) else (
    echo.
    echo =======================================================
    echo Finished installing dependencies for all Maya versions.
    echo =======================================================
    goto PAUSE
)

:PAUSE
pause
goto EOF

:TIMED_EXIT
timeout /t 5 /nobreak

:EOF
endlocal
exit /b