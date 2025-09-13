@echo off
cd /d C:\Users\jainp\rockfall-prediction

REM Virtual environment activate karo
call venv\Scripts\activate

REM Streamlit app run karo
streamlit run app.py

pause

