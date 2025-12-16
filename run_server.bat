@echo off
chcp 65001 >nul
echo ========================================
echo Запуск сервера проверки клинических задач
echo ========================================
echo.
echo Проверка конфигурации...

if not exist .env (
    echo Создание .env файла...
    copy Open_ai.env .env >nul
    echo OK: .env файл создан
) else (
    echo OK: .env файл существует
)

if not exist data\tasks.json (
    echo ОШИБКА: Файл data\tasks.json не найден!
    pause
    exit /b 1
) else (
    echo OK: Файл с задачами найден
)

echo.
echo Запуск сервера на http://localhost:8000
echo.
echo Для остановки нажмите Ctrl+C
echo.
echo Откройте браузер и перейдите на: http://localhost:8000
echo.

python main.py

pause





