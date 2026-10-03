@echo off
rem Noor Tender Suite - full launcher (backend :8000 + frontend :3000 + radar :4318)
title Noor Tender Suite - Full Launcher
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Noor-Demo-Launcher.ps1"
if errorlevel 1 pause
