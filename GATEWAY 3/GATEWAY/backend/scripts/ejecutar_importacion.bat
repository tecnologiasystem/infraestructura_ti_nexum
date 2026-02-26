@echo off
REM Script batch para ejecutar la importación de CSV
echo.
echo ============================================================
echo Importacion de CSV a SQL Server
echo ============================================================
echo.

REM Activar entorno virtual
call env\Scripts\activate.bat

REM Ejecutar script
python scripts\importar_rapido.py

REM Pausa para ver resultados
echo.
pause
