@echo off
call conda activate parade
cd /d %~dp0
streamlit run app.py
pause
