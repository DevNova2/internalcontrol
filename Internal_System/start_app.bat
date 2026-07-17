@echo off

echo  flying...
call "./venv/Scripts/activate"
echo.
cd bokeh_app
python start_app.py
echo.

pause