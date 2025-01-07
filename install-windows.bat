@echo off
setlocal enabledelayedexpansion

REM Check for Python and install if not found
python --version 2>NUL
if errorlevel 1 goto install_python
call :python_installed

REM Function to install Python
:install_python
echo Python not found. Installing Python...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile 'python-installer.exe'"
start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
del python-installer.exe
echo Python installation complete.
exit /b 0

:python_installed

REM Ensure Python is available in the PATH
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python installation failed!
    exit /b 1
)

REM Install venv-run
echo "Installing venv-run"
pip install venv-run

REM Create a virtual environment
echo Creating a virtual environment...
python -m venv .venv

REM Activate the virtual environment
echo Activating the virtual environment...
call .venv\Scripts\activate

REM Create requirements.txt if it doesn't exist
(
    echo requests
    echo jsonschema
    echo feedparser
    echo openai
    echo keyring
    echo windows-curses
    echo packaging
    echo pygooglenews
) > requirements.txt

REM Create start script
echo .venv\Scripts\activate > start.bat
echo python ednasg.py >> start.bat

REM Install required packages
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Print completion message
echo Installation complete! Your virtual environment is ready.
echo You can run your program now by running with .\start.bat or with these commands:
echo .venv\Scripts\activate
echo python ./ednasg.py

pause
endlocal
exit
