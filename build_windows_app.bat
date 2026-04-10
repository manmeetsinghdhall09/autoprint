@echo off
echo Building Auto Print App for Windows...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in your PATH. Please install Python to build the app.
    pause
    exit /b
)

:: Download SumatraPDF if not present (required for native Windows printing)
if not exist "SumatraPDF.exe" (
    echo Downloading portable SumatraPDF for native Windows PDF printing...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/sumatrapdfreader/sumatrapdf/releases/download/prerelease/SumatraPDF-prerelease-64.exe' -OutFile 'SumatraPDF.exe'"
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Build the executable
echo Running PyInstaller...
pyinstaller --noconfirm --onefile --windowed --name "AutoPrintApp" --add-data "SumatraPDF.exe;." "main.py"

echo.
echo =========================================================
echo Build complete! 
echo Your portable executable can be found at: dist\AutoPrintApp.exe
echo =========================================================
pause
