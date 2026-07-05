@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\cha73\anaconda3\envs\ncav\python.exe"
set "PYTHONPATH=%CD%\src"

if not exist "%PYTHON_EXE%" (
    echo Python was not found at:
    echo %PYTHON_EXE%
    echo.
    echo Please check that the ncav conda environment exists.
    pause
    exit /b 1
)

if not exist "data\input" (
    echo data\input folder was not found.
    pause
    exit /b 1
)

if not exist "data\output" mkdir "data\output"
if not exist "data\app" mkdir "data\app"

echo Updating NCAV Screener data...
echo.

if exist "data\input\krx_raw.csv" (
    "%PYTHON_EXE%" -c "from pathlib import Path; from ncav_screener.market_data import convert_krx_raw_to_market_data; convert_krx_raw_to_market_data(Path(r'data\input\krx_raw.csv'), Path(r'data\input\market_data.csv'), source_date='2026-07-03'); print('Updated market data: data\\input\\market_data.csv')"
    if errorlevel 1 (
        echo.
        echo KRX raw market data conversion failed.
        pause
        exit /b 1
    )
)

"%PYTHON_EXE%" -m ncav_screener.cli bulk-ncav ^
    --with-ev-ebit ^
    --with-f-score ^
    --no-default-filters ^
    --max-ratio 1.0 ^
    --max-ev-ebit 5 ^
    --output "data\output\bulk_ncav_ev_ebit_results_fscore.csv" ^
    --candidates-output "data\output\bulk_ncav_candidates_fscore.csv" ^
    --value-candidates-output "data\output\bulk_value_candidates_fscore.csv" ^
    --korean-output "data\output\bulk_value_candidates_fscore_kr.csv"

if errorlevel 1 (
    echo.
    echo Data update failed.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -c "from pathlib import Path; from ncav_screener.reporting import save_korean_report; save_korean_report(Path(r'data\output\bulk_ncav_ev_ebit_results_fscore.csv'), Path(r'data\app\screener_results_kr.csv')); print('Updated app data: data\\app\\screener_results_kr.csv')"

if errorlevel 1 (
    echo.
    echo Korean app CSV update failed.
    pause
    exit /b 1
)

echo.
echo Done. Open the Streamlit app and press the refresh button if it is already running.
pause
