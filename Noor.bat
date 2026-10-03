@echo off
title Noor AI Platform Launcher
rem Runs the launcher that sits next to this file - works from any folder or a Desktop shortcut.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Noor-Launcher.ps1"
if errorlevel 1 pause
