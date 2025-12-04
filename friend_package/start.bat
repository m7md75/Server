@echo off
title WeJZ Client
color 0A
python launcher.py
if errorlevel 1 (
    echo.
    echo Error starting launcher. Make sure Python is installed.
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
)
