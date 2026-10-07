@echo off
:: Drag a folder onto this file to preview how it would be sorted.
cd /d "%~dp0"
if "%~1"=="" (
    set /p TARGET=Folder to sort: 
) else (
    set "TARGET=%~1"
)
python sorter.py "%TARGET%"
echo.
set /p GO=Move the files as shown above? (y/n): 
if /i "%GO%"=="y" python sorter.py "%TARGET%" --apply
pause
