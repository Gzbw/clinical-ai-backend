from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from pathlib import Path
from typing import Optional, List, Dict
import google.generativeai as genai
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

app = FastAPI(title="Clinical AI Backend")

# Настройка CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация Google Gemini клиента
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    print("Предупреждение: GEMINI_API_KEY не найден в .env файле")

# Путь к файлу с задачами
TASKS_FILE = Path("data/tasks.json")


class AnswerRequest(BaseModel):
    answer: str
    task_id: int


def load_tasks() -> Dict:
    """Загружает все задачи из JSON файла"""
    if not TASKS_FILE.exists():
        raise HTTPException(status_code=404, detail=f"Файл {TASKS_FILE} не найден. Создайте файл data/tasks.json")
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_task_by_id(task_id: int) -> Dict:
    """Получает задачу по ID"""
    tasks_data = load_tasks()
    for task in tasks_data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")


def format_task_for_display(task: Dict) -> str:
    """Форматирует задачу для отображения"""
    parts = [
        f"1. Кто заболел: {task.get('patient_info', '')}",
        f"\n2. Жалобы: {task.get('complaints', '')}",
        f"\n3. Anamnesis morbi: {task.get('anamnesis_morbi', '')}",
        f"\n4. Эпидемиологический анамнез: {task.get('epidemiological_history', '')}",
        f"\n5. Объективные данные: {task.get('objective_data', '')}",
        f"\n6. Лабораторные данные: {task.get('laboratory_data', '')}",
        f"\n\nЗадания:"
    ]
    
    for i, task_item in enumerate(task.get('tasks', []), 1):
        parts.append(f"\n{i}. {task_item}")
    
    return "".join(parts)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Главная страница"""
    html_path = Path("static/index.html")
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Clinical AI Backend</h1><p>Создайте файл static/index.html</p>"


@app.get("/api/tasks")
async def get_all_tasks():
    """Получить список всех задач"""
    try:
        tasks_data = load_tasks()
        tasks_list = []
        for task in tasks_data.get("tasks", []):
            tasks_list.append({
                "id": task.get("id"),
                "title": task.get("title", f"Задача {task.get('id')}")
            })
        return {"tasks": tasks_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/task/{task_id}")
async def get_task(task_id: int):
    """Получить конкретную задачу по ID"""
    try:
        task = get_task_by_id(task_id)
        return {
            "id": task.get("id"),
            "title": task.get("title"),
            "task_text": format_task_for_display(task)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/check-answer")
async def check_answer(request: AnswerRequest):
    """Проверить ответ студента по эталону"""
    try:
        # Получаем задачу и эталонный ответ
        task = get_task_by_id(request.task_id)
        reference = task.get("reference_answer", {})
        task_text = format_task_for_display(task)
        
        # Формируем промпт для ИИ с 6 критериями
        prompt = f"""Ты - опытный преподаватель клинической медицины, который проверяет ответы студентов по клиническим задачам.

КЛИНИЧЕСКАЯ ЗАДАЧА:
{task_text}

ЭТАЛОННЫЙ ОТВЕТ (по 6 критериям оценки):

Критерий 1 - Ведущие синдромы заболевания:
{reference.get('criteria_1_syndromes', 'Не указано')}

Критерий 2 - Эпидемиологические данные:
{reference.get('criteria_2_epidemiological', 'Не указано')}

Критерий 3 - Характерные объективные данные:
{reference.get('criteria_3_objective_data', 'Не указано')}

Критерий 4 - Обоснование диагноза:
{reference.get('criteria_4_diagnosis', 'Не указано')}

Критерий 5 - План диагностики:
{reference.get('criteria_5_examination_plan', 'Не указано')}

Критерий 6 - План лечения:
{reference.get('criteria_6_treatment_plan', 'Не указано')}

ОТВЕТ СТУДЕНТА:
{request.answer}

ИНСТРУКЦИЯ:
Проверь ответ студента по каждому из 6 критериев. Учти, что студент может писать своими словами, главное - это правильность и полнота информации. Если что-то отсутствует или неверно, четко укажи это.

Верни ответ в формате JSON со следующей структурой:
{{
    "overall_score": число от 0 до 100 (общая оценка),
    "detailed_feedback": "подробный общий отзыв на русском языке с указанием основных замечаний",
    "criteria_evaluation": {{
        "criteria_1": {{
            "score": число от 0 до 100,
            "feedback": "проверка по критерию 1 - ведущие синдромы. Укажи, что правильно, что отсутствует, что неверно",
            "is_complete": true/false,
            "missing_points": ["что отсутствует в ответе"],
            "incorrect_points": ["что указано неверно"]
        }},
        "criteria_2": {{
            "score": число от 0 до 100,
            "feedback": "проверка по критерию 2 - эпидемиологические данные",
            "is_complete": true/false,
            "missing_points": ["что отсутствует"],
            "incorrect_points": ["что указано неверно"]
        }},
        "criteria_3": {{
            "score": число от 0 до 100,
            "feedback": "проверка по критерию 3 - объективные данные",
            "is_complete": true/false,
            "missing_points": ["что отсутствует"],
            "incorrect_points": ["что указано неверно"]
        }},
        "criteria_4": {{
            "score": число от 0 до 100,
            "feedback": "проверка по критерию 4 - обоснование диагноза",
            "is_complete": true/false,
            "missing_points": ["что отсутствует"],
            "incorrect_points": ["что указано неверно"]
        }},
        "criteria_5": {{
            "score": число от 0 до 100,
            "feedback": "проверка по критерию 5 - план диагностики",
            "is_complete": true/false,
            "missing_points": ["что отсутствует"],
            "incorrect_points": ["что указано неверно"]
        }},
        "criteria_6": {{
            "score": число от 0 до 100,
            "feedback": "проверка по критерию 6 - план лечения",
            "is_complete": true/false,
            "missing_points": ["что отсутствует"],
            "incorrect_points": ["что указано неверно"]
        }}
    }},
    "strengths": ["сильные стороны ответа"],
    "recommendations": ["конкретные рекомендации для улучшения ответа"]
}}

ВАЖНО:
- Будь объективным и конструктивным
- Учти, что студент может выражать мысли своими словами - это нормально
- Главное - это правильность медицинской информации и полнота охвата всех критериев
- Четко указывай, что именно отсутствует или неверно
- Давай конкретные рекомендации для улучшения"""

        # Проверяем наличие API ключа
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="GEMINI_API_KEY не найден. Проверьте файл .env"
            )
        
        # Настраиваем Gemini клиент
        genai.configure(api_key=api_key)
        
        # Пробуем несколько моделей Gemini (используем правильные названия с префиксом models/)
        models_to_try = ["models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-pro-latest", "models/gemini-flash-latest"]
        result_text = None
        last_error = None
        
        # Формируем полный промпт с инструкцией для JSON
        full_prompt = f"""Ты - опытный преподаватель клинической медицины, который проверяет ответы студентов. Всегда отвечай на русском языке в формате JSON.

{prompt}

ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста до или после него."""

        for model_name in models_to_try:
            try:
                # Создаем модель с конфигурацией для JSON ответа
                generation_config = {
                    "temperature": 0.3,
                    "response_mime_type": "application/json",
                }
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config
                )
                
                # Отправляем запрос
                response = model.generate_content(full_prompt)
                
                # Получаем текст ответа
                if hasattr(response, 'text'):
                    result_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    result_text = response.candidates[0].content.parts[0].text
                else:
                    result_text = str(response)
                
                if result_text and result_text.strip():
                    break  # Если успешно, выходим из цикла
                    
            except Exception as gemini_error:
                last_error = gemini_error
                error_str = str(gemini_error).lower()
                
                # Если это ошибка аутентификации, не пробуем другие модели
                if "api_key" in error_str or "authentication" in error_str or "permission" in error_str:
                    break
                # Если модель не найдена, пробуем следующую
                if "not found" in error_str or "notfound" in error_str:
                    continue
                # Пробуем следующую модель
                continue
        
        # Если все модели не сработали
        if not result_text:
            error_message = str(last_error) if last_error else "Неизвестная ошибка"
            error_str_lower = error_message.lower()
            
            if "api_key" in error_str_lower or "authentication" in error_str_lower or "permission" in error_str_lower:
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка аутентификации Google Gemini API. Проверьте API ключ в файле .env"
                )
            elif "quota" in error_str_lower or "rate limit" in error_str_lower:
                raise HTTPException(
                    status_code=500,
                    detail="Превышен лимит запросов к Google Gemini API. Подождите немного и попробуйте снова."
                )
            elif "safety" in error_str_lower or "blocked" in error_str_lower:
                raise HTTPException(
                    status_code=500,
                    detail="Запрос был заблокирован системой безопасности Gemini. Попробуйте переформулировать запрос."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка Google Gemini API: {error_message[:200]}"
                )
        
        # Очищаем ответ от возможных markdown блоков кода
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()
        
        # Пытаемся распарсить JSON
        try:
            result_json = json.loads(result_text)
            return result_json
        except json.JSONDecodeError as e:
            # Если не удалось распарсить, пытаемся найти JSON в тексте
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result_json = json.loads(json_match.group(0))
                    return result_json
                except:
                    pass
            
            # Если все не удалось, возвращаем базовую структуру
            return {
                "overall_score": 50,
                "detailed_feedback": f"Ошибка парсинга ответа ИИ. Полученный ответ: {result_text[:500]}",
                "criteria_evaluation": {},
                "strengths": [],
                "recommendations": ["Попробуйте проверить ответ еще раз"],
                "error": f"Не удалось распарсить ответ ИИ: {str(e)}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        # Логируем полную информацию об ошибке для отладки
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка в check_answer: {error_details}")  # Вывод в консоль для отладки
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при проверке ответа: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

