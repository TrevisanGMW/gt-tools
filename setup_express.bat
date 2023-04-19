@echo off

REM v1.0.0 - 2020-11-08 - Initial Release
REM v1.0.1 - 2020-12-03 - Added exist checks
REM v1.0.2 - 2021-01-28 - Updated uninstaller with new scripts
REM v1.1.0 - 2021-05-18 - Added support for paths with spaces
REM v1.2.0 - 2022-03-14 - Changed python target to scripts\gt_tools (No more entries to uninstall function)

@title =  Auto Installer for GT Tools
SET CopyDirDestination=%UserProfile%\Documents\maya
SET CopyDirSource=%~dp0
SET CopyDirSourceGlobal=%UserProfile%\Documents\maya\scripts
SET CopyDirSourceMel=%~dp0mel-scripts
SET CopyDirSourcePy=%~dp0python-scripts
SET ImportCommandSearch=source\ \"gt_tools_menu.mel\";
SET ImportCommand=source "gt_tools_menu.mel";
SET ManualInstallationURL=https://github.com/TrevisanGMW/gt-tools
SET ExtractionDirPython=%~dp0python-scripts
SET ExtractionDirMel=%~dp0mel-scripts

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
@echo. 	1 = Install GT Tools
@echo. 	2 = Uninstall GT Tools
@echo. 	3 = About Installer
@echo.
@echo.
@echo off
SET /P M=Type 1, 2 or 3 then press ENTER:
IF %M%==1 GOTO INSTALL
IF %M%==2 GOTO UNINSTALL
IF %M%==3 GOTO ABOUT
GOTO EOF

REM Main Function
:INSTALL

IF NOT EXIST %ExtractionDirPython% ( GOTO SETUP_MISSING_SCRIPTS ) 
IF NOT EXIST %ExtractionDirMel% ( GOTO SETUP_MISSING_SCRIPTS ) 
IF EXIST %CopyDirDestination% (
	GOTO valid_maya_dir
) ELSE (
	GOTO missing_maya_dir
)

:valid_maya_dir
CD /D %CopyDirDestination%
for /D %%s in (.\*) do CALL :get_maya_folders %%s
CALL :valid_maya_dir_global
IF %RobocopyError%==1 GOTO robocopy_error
GOTO INSTALLATION_COMPLETE
EXIT /B %ERRORLEVEL% 

REM Start installation for every version
:get_maya_folders
echo %~1|findstr /r "[0-9][0-9][0-9][0-9]" >nul  && ( CALL :build_path %%~1 )
EXIT /B 0

:build_path
SET version=%~1
SET version_no_dot=%version:.=%
CALL :copy_files %CopyDirDestination%%version_no_dot%\scripts
CALL :check_usersetup_existence %CopyDirDestination%%version_no_dot%\scripts
EXIT /B 0

:copy_files
SET RobocopyError=0
ROBOCOPY "%CopyDirSource% " "%~1\gt_tools" /Z /IF "*.py" /njh /njs /ndl /nc /ns
IF %ERRORLEVEL%==16 SET RobocopyError=1
ROBOCOPY "%CopyDirSource% " "%~1 "  /Z /IF "*.mel" /njh /njs /ndl /nc /ns
IF %ERRORLEVEL%==16 SET RobocopyError=1
IF EXIST "%CopyDirSourceMel% " (
	ROBOCOPY "%CopyDirSourceMel% " "%~1 "  /Z /IF "*.mel" /XF "userSetup*" /njh /njs /ndl /nc /ns
	IF %ERRORLEVEL%==16 SET RobocopyError=1
) 
IF EXIST "%CopyDirSourcePy% " (
	ROBOCOPY "%CopyDirSourcePy%" "%~1\gt_tools"  /Z /IF "*.py" /njh /njs /ndl /nc /ns
	IF %ERRORLEVEL%==16 SET RobocopyError=1
) 
EXIT /B 0

:check_usersetup_existence
SET UserSetupPath=%~1\userSetup.mel
IF EXIST %UserSetupPath% ( CALL :check_import_existence %UserSetupPath% ) ELSE ( CALL :create_new_usersetup %UserSetupPath% )
EXIT /B 0

:check_import_existence
>nul findstr "%ImportCommandSearch%" %~1 && (
  REM import already present
) || (
  CALL :add_import %~1
)
EXIT /B 0

:add_import
ECHO. >> %~1
echo %ImportCommand% >> %~1
EXIT /B 0

:create_new_usersetup
echo %ImportCommand% >> %~1
EXIT /B 0


REM Global userSetup Check
:valid_maya_dir_global
IF EXIST %CopyDirSourceGlobal% ( CALL :check_usersetup_existence_global ) 
EXIT /B 0

:check_usersetup_existence_global
SET GlobalUsersetupPath=%CopyDirSourceGlobal%\userSetup.mel
IF EXIST %GlobalUsersetupPath% ( CALL :global_usersetup_exists %GlobalUsersetupPath% ) 
EXIT /B 0

:global_usersetup_exists
>nul findstr "%ImportCommandSearch%" %~1 && (
  REM import already present
) || (
  CALL :add_import_global_usersetup %~1
)
EXIT /B 0

:add_import_global_usersetup
ECHO. >> %~1
echo %ImportCommand% >> %~1
EXIT /B 0


REM Start uninstall
:UNINSTALL
tasklist /FI "IMAGENAME eq maya.exe" | findstr "maya.exe" >nul
IF %ERRORLEVEL% == 1 GOTO APP_NOT_RUNNING_UNINSTALL
GOTO APP_RUNNING_UNINSTALL

:APP_NOT_RUNNING_UNINSTALL
IF EXIST %CopyDirDestination% (
	GOTO VALID_MAYA_DIR_UNINSTALL
) ELSE (
	GOTO MISSING_MAYA_DIR_UNINSTALL
)

:VALID_MAYA_DIR_UNINSTALL
CD /D %CopyDirDestination%
for /D %%s in (.\*) do CALL :get_maya_folders_uninstall %%s
CALL :check_usersetup_existence_global_uninstall
GOTO UNINSTALLATION_COMPLETE
EXIT /B %ERRORLEVEL% 

:get_maya_folders_uninstall
echo %~1|findstr /r "[0-9][0-9][0-9][0-9]" >nul  && ( CALL :build_path_uninstall %%~1 )
EXIT /B 0

:build_path_uninstall
SET version=%~1
SET version_no_dot=%version:.=%
CALL :remove_files %CopyDirDestination%%version_no_dot%\scripts
CALL :check_usersetup_existence_uninstall %CopyDirDestination%%version_no_dot%\scripts
EXIT /B 0

:remove_files
del %~1\gt_tools_menu.mel
del %~1\gt_connect_attributes.py
del %~1\gt_connect_attributes.pyc
del %~1\gt_create_ctrl_auto_fk.py
del %~1\gt_create_ctrl_auto_fk.pyc
del %~1\gt_create_ctrl_auto_FK.py
del %~1\gt_create_ctrl_auto_FK.pyc
del %~1\gt_create_ctrl_simple_ik_leg.py
del %~1\gt_create_ctrl_simple_ik_leg.pyc
del %~1\gt_generate_icons.py
del %~1\gt_generate_icons.pyc
del %~1\gt_generate_inbetween.py
del %~1\gt_generate_inbetween.pyc
del %~1\gt_generate_python_curve.py
del %~1\gt_generate_python_curve.pyc
del %~1\gt_generate_text_curve.py
del %~1\gt_generate_text_curve.pyc
del %~1\gt_make_stretchy_leg.py
del %~1\gt_make_stretchy_leg.pyc
del %~1\gt_maya_to_discord.py
del %~1\gt_maya_to_discord.pyc
del %~1\gt_mirror_cluster_tool.py
del %~1\gt_mirror_cluster_tool.pyc
del %~1\gt_renamer.py
del %~1\gt_renamer.pyc
del %~1\gt_render_checklist.py
del %~1\gt_render_checklist.pyc
del %~1\gt_replace_reference_paths.py
del %~1\gt_replace_reference_paths.pyc
del %~1\gt_selection_manager.py
del %~1\gt_selection_manager.pyc
del %~1\gt_transfer_transforms.py
del %~1\gt_transfer_transforms.pyc
del %~1\gt_utilities.py
del %~1\gt_utilities.pyc
del %~1\gt_api.py
del %~1\gt_api.pyc
del %~1\gt_create_sphere_types.py
del %~1\gt_create_sphere_types.pyc
del %~1\gt_create_auto_fk.py
del %~1\gt_create_auto_fk.pyc
del %~1\gt_create_ik_leg.py
del %~1\gt_create_ik_leg.pyc
del %~1\gt_path_manager.py
del %~1\gt_path_manager.pyc
del %~1\gt_check_for_updates.py
del %~1\gt_check_for_updates.pyc
del %~1\gt_color_manager.py
del %~1\gt_color_manager.pyc
del %~1\gt_startup_booster.py
del %~1\gt_startup_booster.pyc
del %~1\gt_fspy_importer.py
del %~1\gt_fspy_importer.pyc
del %~1\gt_auto_biped_rigger.py
del %~1\gt_auto_biped_rigger.pyc
del %~1\gt_make_ik_stretchy.py
del %~1\gt_make_ik_stretchy.pyc
del %~1\gt_add_sine_attributes.py
del %~1\gt_add_sine_attributes.pyc
del %~1\gt_create_testing_keys.py
del %~1\gt_tools /Q /S
rmdir %~1\gt_tools /Q /S
EXIT /B 0


:check_usersetup_existence_global_uninstall
SET GlobalUsersetupPath=%CopyDirSourceGlobal%\userSetup.mel
IF EXIST %GlobalUsersetupPath% ( CALL :global_usersetup_exists_uninstall %GlobalUsersetupPath% ) 
EXIT /B 0

:global_usersetup_exists_uninstall
>nul findstr "%ImportCommandSearch%" %~1 && ( CALL :remove_import %~1 ) 
EXIT /B 0

:check_usersetup_existence_uninstall
SET UserSetupPath=%~1\userSetup.mel
IF EXIST %UserSetupPath% ( CALL :check_import_existence_uninstall %UserSetupPath% )
EXIT /B 0

:check_import_existence_uninstall
>nul findstr "%ImportCommandSearch%" %~1 && ( CALL :remove_import %~1 ) 
EXIT /B 0

:remove_import
SET "TEMP_USERSETUP=%TEMP%\%RANDOM%__hosts"
findstr /V "%ImportCommandSearch%" "%~1" > "%TEMP_USERSETUP%"
COPY /b/v/y "%TEMP_USERSETUP%" "%~1"
(for /f usebackq^ eol^= %%a in (%~1) do break) && echo userSetup has data || del %~1
EXIT /B 0



REM Install Feedback
:missing_maya_dir
@echo off
color 0C
cls
@echo on
@echo.
@echo.
@echo       ллллллл лллллл  лллллл   лллллл  лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллл   лллллл  лллллл  лл    лл лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллллл лл   лл лл   лл  лллллл  лл   лл 
@echo.
@echo.
@echo       Maya directory was not found. 
@echo       You might have to install the scripts manually.
@echo       Learn how to fix this issue in the "About Installer" option.
@echo.
@echo.
@echo off
SET /P AREYOUSURE=Would you like to open the instructions for the manual installation (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO EOF
start "" %ManualInstallationURL%
GOTO EOF

:robocopy_error
@echo off
color 0C
cls
@echo on
@echo.
@echo.
@echo       ллллллл лллллл  лллллл   лллллл  лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллл   лллллл  лллллл  лл    лл лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллллл лл   лл лл   лл  лллллл  лл   лл 
@echo.
@echo.
@echo       An error was raised when copying the files. 
@echo       The installation might have succeeded, but the script can't confirm that. 
@echo       You might have to install the scripts manually.
@echo       Learn how to possibly fix this issue in the "About Installer" option.
@echo.
@echo.
@echo off
SET /P AREYOUSURE=Would you like to open the instructions for the manual installation (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO EOF
start "" %ManualInstallationURL%
GOTO EOF

:INSTALLATION_COMPLETE
@echo off
color 0A
cls
@echo on
@echo.   
@echo.                                   
@echo       лллллл   лллллл  ллл    лл ллллллл 
@echo       лл   лл лл    лл лллл   лл лл      
@echo       лл   лл лл    лл лл лл  лл ллллл   
@echo       лл   лл лл    лл лл  лл лл лл      
@echo       лллллл   лллллл  лл   лллл ллллллл 
@echo.     
@echo.  
@echo       Please restart Maya to load scripts.
@echo.  
@echo. 
@echo off      
pause               
GOTO EOF

REM Uninstall Feedback
:MISSING_MAYA_DIR_UNINSTALL
@echo off
color 0C
cls
@echo on
@echo.
@echo.
@echo       ллллллл лллллл  лллллл   лллллл  лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллл   лллллл  лллллл  лл    лл лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллллл лл   лл лл   лл  лллллл  лл   лл 
@echo.
@echo.
@echo       Maya directory was not found. 
@echo       You might have to uninstall the scripts manually.
@echo       Learn how to fix this issue in the "About Installer" option.
@echo.
@echo.
@echo off
SET /P AREYOUSURE=Would you like to open the instructions for the manual uninstallation (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO EOF
start "" %ManualInstallationURL%
GOTO EOF


:APP_RUNNING_UNINSTALL
@echo off
color 0C
cls
@echo on
@echo.
@echo.
@echo       ллллллл лллллл  лллллл   лллллл  лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллл   лллллл  лллллл  лл    лл лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллллл лл   лл лл   лл  лллллл  лл   лл 
@echo.
@echo.
@echo       Process named "maya.exe" was found.
@echo       Please close Maya before uninstalling.
@echo.
@echo.
@echo off
pause
GOTO MENU


:UNINSTALLATION_COMPLETE
@echo off
color 0A
cls
@echo on
@echo.   
@echo.                                   
@echo       лллллл   лллллл  ллл    лл ллллллл 
@echo       лл   лл лл    лл лллл   лл лл      
@echo       лл   лл лл    лл лл лл  лл ллллл   
@echo       лл   лл лл    лл лл  лл лл лл      
@echo       лллллл   лллллл  лл   лллл ллллллл 
@echo.     
@echo.  
@echo       Scripts were removed.
@echo       Import line was erased from userSetup.mel
@echo.  
@echo. 
@echo off      
pause                   
GOTO EOF


:SETUP_MISSING_SCRIPTS
@echo off
color 0C
cls
@echo on
@echo.
@echo.
@echo       ллллллл лллллл  лллллл   лллллл  лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллл   лллллл  лллллл  лл    лл лллллл  
@echo       лл      лл   лл лл   лл лл    лл лл   лл 
@echo       ллллллл лл   лл лл   лл  лллллл  лл   лл 
@echo.
@echo.
@echo       The setup file can't find the scripts.
@echo       Missing "mel-scripts" or "python-scripts".
@echo       Did you properly extract the files before running it?
@echo.
@echo.
@echo off
pause
GOTO MENU


:ABOUT
@echo off
color 02
cls
@echo on
@echo.
@echo.                _
@echo.               ( )                 GT Tools Setup
@echo.                H                  
@echo.                H                  This batch file attempts to automatically install all python and mel
@echo.               _H_                 scripts for GT Tools so the user doesn't need to mannualy copy them.
@echo.            .-'-.-'-.
@echo.           /         \             It assumes that Maya preferences are stored in the default path
@echo.          !           !            under "Documents\maya\####"  (#### being the version number)
@echo.          !   .-------'._          
@echo.          !  / /  '.' '. \         This is what the script does when installing:
@echo.          !  \ \ @   @ / /         1. It copies necessary scripts to all "maya\####\scripts" folders.
@echo.          !   '---------'          2. It looks for the "userSetup.mel" file to add the initialization line.
@echo.          !    _______!            (This process will not affect existing lines inside your "userSetup.mel")
@echo.          !  .'-+-+-+!             3. If "userSetup.mel" is not found, one will be created.
@echo.          !  '.-+-+-+!             
@echo.          !    """""" !            This is what the script does when uninstalling:
@echo.          '-._______.-'            1. It removes the installed scripts.
@echo.                                   2. It removes the initialization lines from all "userSetup.mel" files.
@echo. 
@echo. 
@echo. 
@echo off
pause
GOTO MENU

:EOF
EXIT