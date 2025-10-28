@echo off
REM Build script for TwinCAT HMI Application

echo ========================================
echo Building TwinCAT HMI Application
echo ========================================

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building executable...
echo.

REM Build with PyInstaller
pyinstaller --name="TwinCAT_HMI" ^
    --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --add-data "config.json;." ^
    --hidden-import="PyQt5" ^
    --hidden-import="pyads" ^
    --hidden-import="matplotlib" ^
    --collect-all pyads ^
    main.py

if errorlevel 1 (
    echo.
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo Executable location: dist\TwinCAT_HMI.exe
echo ========================================
echo.

REM Create release folder
if not exist "release" mkdir release

REM Copy executable
copy "dist\TwinCAT_HMI.exe" "release\" >nul

REM Copy config template
copy "config.json" "release\config_template.json" >nul

REM Create README for release
echo TwinCAT HMI Application > release\README.txt
echo. >> release\README.txt
echo 1. Copy config_template.json to config.json >> release\README.txt
echo 2. Edit config.json with your PLC settings >> release\README.txt
echo 3. Run TwinCAT_HMI.exe >> release\README.txt
echo. >> release\README.txt
echo Logs will be created in alarm_logs folder >> release\README.txt

echo.
echo Release package created in 'release' folder
echo.
pause
