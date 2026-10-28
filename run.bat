@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set PY=.venv\Scripts\python.exe

if not exist models\sentiment_model.joblib (
  echo [1/5] Gjenerimi i te dhenave...
  %PY% data\generate_dataset.py || goto :err
  %PY% data\generate_business.py || goto :err
  echo [2/5] Pastrimi...
  %PY% -m src.data || goto :err
  echo [3/5] Grafiket...
  %PY% -m src.visualize || goto :err
  echo [4/5] Trajnimi...
  %PY% -m src.train || goto :err
)

if not exist frontend\dist\index.html (
  echo [5/5] Ndertimi i nderfaqes React...
  where npm >nul 2>nul && (
    pushd frontend
    call npm install --no-audit --no-fund && call npm run build
    popd
  ) || echo Node.js mungon: do perdoret nderfaqja e thjeshte.
)

%PY% -m pytest -q || goto :err
echo.
echo Hap: http://127.0.0.1:5000
%PY% app.py
goto :eof

:err
echo Dicka deshtoi. Shiko mesazhin me siper.
pause
