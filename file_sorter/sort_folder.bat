@echo off
:: Drag a folder onto this file: it previews the sort, then asks before moving anything.
cd /d "%~dp0"
if "%~1"=="" (
    set /p TARGET=Folder to sort: 
) else (
    set "TARGET=%~1"
)
python sorter.py "%TARGET%" --ask
pause
