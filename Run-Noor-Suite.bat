@echo off
rem Noor Tender Suite — full launcher (backend :8000 + frontend :3000 + radar :4318)
chcp 65001 >nul
title منظومة النور — التشغيل الكامل
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Noor-Demo-Launcher.ps1"
if errorlevel 1 pause
