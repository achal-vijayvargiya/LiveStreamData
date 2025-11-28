@echo off
call venv\Scripts\activate.bat
cd app\websocket
python server.py
pause

