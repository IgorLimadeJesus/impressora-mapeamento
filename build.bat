@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul || (
  echo Python Launcher nao encontrado. Instale o Python 3.12 ou superior.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python tools\generate_icon.py
if errorlevel 1 exit /b 1
python -m pytest -q
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean USB-LPT-Mapper.spec
if errorlevel 1 exit /b 1

echo.
echo Executavel criado em dist\USB-LPT-Mapper.exe
endlocal
