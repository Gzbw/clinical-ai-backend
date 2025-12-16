@echo off
echo ========================================
echo Запуск системы проверки клинических задач
echo ========================================
echo.

REM Проверка существования .env файла
if not exist .env (
    echo Создание .env файла из Open_ai.env...
    copy Open_ai.env .env >nul
    echo .env файл создан
    echo.
)

echo Проверка зависимостей...
python -c "import fastapi, uvicorn, openai" 2>nul
if errorlevel 1 (
    echo Установка зависимостей...
    pip install -r requirements.txt
    echo.
)

echo Запуск сервера...
echo Сервер будет доступен по адресу: http://localhost:8000
echo Для остановки нажмите Ctrl+C
echo.
python main.py





