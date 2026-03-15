@echo off
:: One-click installer wrapper — runs install.ps1
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
pause
