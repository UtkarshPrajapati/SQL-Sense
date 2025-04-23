@echo off
cd C:\Users\utkar\OneDrive\Desktop\SQLLLM

if not exist logs mkdir logs

call .\SQLLLM\Scripts\activate

start cmd /k "uvicorn api:app --port 8012 --host 0.0.0.0 --reload > logs/api.log 2>&1"
start cmd /k "python ui.py > logs/ui.log 2>&1"