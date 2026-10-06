@echo off
setlocal enabledelayedexpansion
title AI Health Copilot Engine

:MENU
cls
echo.
echo  ============================================================
echo       AI HEALTH COPILOT ENGINE - Medical Document AI
echo  ============================================================
echo.
echo   [W]  LAUNCH STREAMLIT WEB UI DASHBOARD (Recommended!)
echo   [1]  Prescription images (samples)
echo   [2]  Lab Report images (samples)
echo   [3]  Discharge Summary PDF (samples)
echo   [4]  Tamil Bilingual document (samples)
echo   [5]  YOUR OWN file (custom path)
echo   [6]  Run ALL sample files (batch)
echo   [7]  Run Evaluation (eval.py)
echo   [8]  Run Tests (pytest)
echo   [9]  Install dependencies
echo   [0]  Exit
echo.
echo  ============================================================
set "CHOICE="
set /p CHOICE="  Enter choice (W, 0-9): "
echo.

if /i "!CHOICE!"=="W" goto WEBUI
if "!CHOICE!"=="1" goto PRESCRIPTION
if "!CHOICE!"=="2" goto LAB
if "!CHOICE!"=="3" goto DISCHARGE
if "!CHOICE!"=="4" goto TAMIL
if "!CHOICE!"=="5" goto CUSTOM
if "!CHOICE!"=="6" goto BATCH
if "!CHOICE!"=="7" goto EVAL
if "!CHOICE!"=="8" goto TESTS
if "!CHOICE!"=="9" goto INSTALL
if "!CHOICE!"=="0" goto END

echo  Invalid choice. Try again.
timeout /t 2 >nul
goto MENU

:WEBUI
echo  Starting Streamlit Web Dashboard...
echo  ------------------------------------------------------------
echo  Opening in your default browser at http://localhost:8501
streamlit run app.py
goto MENU

:PRESCRIPTION
echo  Running PRESCRIPTION samples...
echo  ------------------------------------------------------------
echo.
echo  [1/3] prescription1.jpg
python -m ai_engine.cli samples\prescription1.jpg --lang auto
echo.
echo  [2/3] prescription2.jpg
python -m ai_engine.cli samples\prescription2.jpg --lang auto
echo.
echo  [3/3] handwritten1.jpg
python -m ai_engine.cli samples\handwritten1.jpg --lang auto
echo.
echo  Done!
pause
goto MENU

:LAB
echo  Running LAB REPORT samples...
echo  ------------------------------------------------------------
echo.
echo  [1/4] lab1.jpg
python -m ai_engine.cli samples\lab1.jpg --lang auto
echo.
echo  [2/4] lab2.jpg
python -m ai_engine.cli samples\lab2.jpg --lang auto
echo.
echo  [3/4] lab3.jpg
python -m ai_engine.cli samples\lab3.jpg --lang auto
echo.
echo  [4/4] lab4.jpg
python -m ai_engine.cli samples\lab4.jpg --lang auto
echo.
echo  Done!
pause
goto MENU

:DISCHARGE
echo  Running DISCHARGE SUMMARY PDF samples...
echo  ------------------------------------------------------------
echo.
echo  [1/2] discharge1.pdf
python -m ai_engine.cli samples\discharge1.pdf --mime application/pdf
echo.
echo  [2/2] discharge2.pdf
python -m ai_engine.cli samples\discharge2.pdf --mime application/pdf
echo.
echo  Done!
pause
goto MENU

:TAMIL
echo  Running TAMIL Bilingual document...
echo  ------------------------------------------------------------
echo.
python -m ai_engine.cli samples\tamil_mixed1.jpg --lang ta
echo.
echo  Done!
pause
goto MENU

:CUSTOM
echo  Run YOUR OWN file
echo  ------------------------------------------------------------
echo  Example: C:\Users\YourName\Downloads\prescription.jpg
echo.
set "FILEPATH="
set /p FILEPATH="  Enter full file path: "
echo.

if not exist "!FILEPATH!" (
    echo  ERROR: File not found: !FILEPATH!
    timeout /t 3 >nul
    goto MENU
)

set "LANG=auto"
set /p LANG="  Language? (auto / en / ta) [Enter = auto]: "
if "!LANG!"=="" set "LANG=auto"

echo.
echo  Processing: !FILEPATH!
echo  ------------------------------------------------------------
python -m ai_engine.cli "!FILEPATH!" --lang !LANG!
echo.
echo  Done!
pause
goto MENU

:BATCH
echo  Running ALL sample files...
echo  ------------------------------------------------------------
echo.
echo  [1] prescription1.jpg
python -m ai_engine.cli samples\prescription1.jpg --lang auto
echo.
echo  [2] prescription2.jpg
python -m ai_engine.cli samples\prescription2.jpg --lang auto
echo.
echo  [3] prescription3.jpg
python -m ai_engine.cli samples\prescription3.jpg --lang auto
echo.
echo  [4] handwritten1.jpg
python -m ai_engine.cli samples\handwritten1.jpg --lang auto
echo.
echo  [5] lab1.jpg
python -m ai_engine.cli samples\lab1.jpg --lang auto
echo.
echo  [6] lab2.jpg
python -m ai_engine.cli samples\lab2.jpg --lang auto
echo.
echo  [7] lab3.jpg
python -m ai_engine.cli samples\lab3.jpg --lang auto
echo.
echo  [8] lab4.jpg
python -m ai_engine.cli samples\lab4.jpg --lang auto
echo.
echo  [9] diagnostic1.jpg
python -m ai_engine.cli samples\diagnostic1.jpg --lang auto
echo.
echo  [10] tamil_mixed1.jpg
python -m ai_engine.cli samples\tamil_mixed1.jpg --lang ta
echo.
echo  [11] discharge1.pdf
python -m ai_engine.cli samples\discharge1.pdf --mime application/pdf
echo.
echo  [12] discharge2.pdf
python -m ai_engine.cli samples\discharge2.pdf --mime application/pdf
echo.
echo  All done!
pause
goto MENU

:EVAL
echo  Running Evaluation Pipeline (eval.py)...
echo  ------------------------------------------------------------
echo.
python eval.py
echo.
echo  Done!
pause
goto MENU

:TESTS
echo  Running Test Suite (pytest)...
echo  ------------------------------------------------------------
echo.
pytest tests\ -v
echo.
echo  Done!
pause
goto MENU

:INSTALL
echo  Installing dependencies from requirements.txt...
echo  ------------------------------------------------------------
echo.
pip install -r requirements.txt
echo.
echo  Done!
pause
goto MENU

:END
echo.
echo  Goodbye! AI Health Copilot Engine closed.
echo.
timeout /t 2 >nul
endlocal
exit /b 0
