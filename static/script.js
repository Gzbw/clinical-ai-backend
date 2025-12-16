const API_BASE = 'http://localhost:8000/api';

// Функция проверки доступности сервера
async function checkServerConnection() {
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        return response.ok;
    } catch (error) {
        console.error('Сервер недоступен:', error);
        return false;
    }
}

let currentTaskId = null;

// Загружаем список задач при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    // Показываем дисклеймер при загрузке страницы
    showDisclaimer();
    
    // Проверяем доступность сервера перед загрузкой задач
    const serverAvailable = await checkServerConnection();
    if (!serverAvailable) {
        const select = document.getElementById('task-select');
        select.innerHTML = '<option value="">⚠️ Сервер не запущен. Запустите: python main.py</option>';
        console.error('Сервер недоступен. Убедитесь, что сервер запущен на http://localhost:8000');
    } else {
        await loadTasksList();
    }
    
    // Обработчик изменения выбранной задачи
    document.getElementById('task-select').addEventListener('change', async (e) => {
        const taskId = parseInt(e.target.value);
        if (taskId) {
            currentTaskId = taskId;
            await loadTask(taskId);
        } else {
            currentTaskId = null;
            document.getElementById('task-content').innerHTML = 
                '<p class="loading">Выберите задачу из списка выше</p>';
        }
    });
});

// Функция показа дисклеймера
function showDisclaimer() {
    const modal = document.getElementById('disclaimer-modal');
    const acceptButton = document.getElementById('accept-button');
    const declineButton = document.getElementById('decline-button');
    
    // Всегда показываем модальное окно при загрузке страницы
    modal.classList.add('show');
    
    // Отключаем кнопку согласия изначально
    acceptButton.disabled = true;
    acceptButton.textContent = 'Я согласен и обязуюсь соблюдать условия (ожидайте 10 секунд)';
    
    // Добавляем элемент для таймера
    const timerInfo = document.createElement('div');
    timerInfo.className = 'timer-info';
    timerInfo.id = 'timer-info';
    acceptButton.parentElement.insertBefore(timerInfo, acceptButton);
    
    // Запускаем таймер на 10 секунд
    let timeLeft = 10;
    timerInfo.textContent = `Пожалуйста, прочитайте условия. Кнопка будет доступна через ${timeLeft} секунд...`;
    
    const countdown = setInterval(() => {
        timeLeft--;
        if (timeLeft > 0) {
            timerInfo.textContent = `Пожалуйста, прочитайте условия. Кнопка будет доступна через ${timeLeft} ${timeLeft === 1 ? 'секунду' : timeLeft < 5 ? 'секунды' : 'секунд'}...`;
        } else {
            clearInterval(countdown);
            timerInfo.textContent = 'Теперь вы можете принять условия';
            acceptButton.disabled = false;
            acceptButton.textContent = 'Я согласен и обязуюсь соблюдать условия';
            // Удаляем элемент таймера через 2 секунды
            setTimeout(() => {
                timerInfo.remove();
            }, 2000);
        }
    }, 1000);
    
    // Обработчик принятия условий
    acceptButton.addEventListener('click', () => {
        modal.classList.remove('show');
    });
    
    // Обработчик отказа
    declineButton.addEventListener('click', () => {
        alert('Вы не согласились с условиями использования. Доступ к сайту запрещен.');
        window.location.href = 'https://www.instagram.com/gzbww/';
    });
    
    // Предотвращаем закрытие модального окна кликом вне его
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            // Можно оставить пустым или показать предупреждение
        }
    });
}

// Загрузка списка задач
async function loadTasksList() {
    try {
        const response = await fetch(`${API_BASE}/tasks`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const select = document.getElementById('task-select');
        select.innerHTML = '<option value="">Выберите задачу...</option>';
        
        if (data.tasks && data.tasks.length > 0) {
            data.tasks.forEach(task => {
                const option = document.createElement('option');
                option.value = task.id;
                option.textContent = task.title;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">Задачи не найдены</option>';
        }
    } catch (error) {
        console.error('Ошибка загрузки задач:', error);
        const select = document.getElementById('task-select');
        select.innerHTML = `<option value="">Ошибка загрузки задач: ${error.message}</option>`;
        
        // Показываем более детальную информацию об ошибке
        if (error.message.includes('Failed to fetch')) {
            console.error('Сервер не отвечает. Убедитесь, что сервер запущен на http://localhost:8000');
        }
    }
}

// Загрузка конкретной задачи
async function loadTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/task/${taskId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        document.getElementById('task-content').textContent = data.task_text;
    } catch (error) {
        console.error('Ошибка загрузки задачи:', error);
        document.getElementById('task-content').innerHTML = 
            `<p style="color: red;">Ошибка загрузки задачи: ${error.message}</p>
             <p style="color: #666; font-size: 0.9em; margin-top: 10px;">
             Убедитесь, что сервер запущен. Запустите: python main.py</p>`;
        
        if (error.message.includes('Failed to fetch')) {
            console.error('Сервер не отвечает. Проверьте, что сервер запущен на http://localhost:8000');
        }
    }
}

// Проверка ответа
document.getElementById('check-button').addEventListener('click', async () => {
    if (!currentTaskId) {
        alert('Пожалуйста, выберите задачу из списка');
        return;
    }

    const answer = document.getElementById('answer-input').value.trim();
    
    if (!answer) {
        alert('Пожалуйста, введите ваш ответ');
        return;
    }

    const checkButton = document.getElementById('check-button');
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');

    // Блокируем кнопку и показываем загрузку
    checkButton.disabled = true;
    checkButton.textContent = 'Проверка...';
    resultsSection.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/check-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                answer: answer,
                task_id: currentTaskId
            })
        });

        if (!response.ok) {
            // Пытаемся получить детальную информацию об ошибке
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // Если не удалось распарсить JSON, используем стандартное сообщение
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();
        displayResults(result);
        resultsSection.style.display = 'block';
        
        // Прокручиваем к результатам
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        resultsContent.innerHTML = 
            `<p style="color: red;">Ошибка при проверке ответа: ${error.message}</p>`;
        resultsSection.style.display = 'block';
    } finally {
        checkButton.disabled = false;
        checkButton.textContent = 'Проверить ответ';
    }
});

// Отображение результатов
function displayResults(result) {
    const resultsContent = document.getElementById('results-content');
    
    const score = result.overall_score || result.score || 0;
    
    // Определяем класс для оценки
    let scoreClass = 'poor';
    if (score >= 80) scoreClass = 'excellent';
    else if (score >= 60) scoreClass = 'good';
    else if (score >= 40) scoreClass = 'average';

    let html = `
        <div class="score ${scoreClass}">
            Общая оценка: ${score}/100
        </div>
        
        <div class="feedback-section">
            <h3>Общий отзыв</h3>
            <p>${result.detailed_feedback || result.feedback || 'Отзыв не предоставлен'}</p>
        </div>
    `;

    // Детальная проверка по 6 критериям
    if (result.criteria_evaluation) {
        html += `
            <div class="feedback-section">
                <h3>Детальная проверка по критериям</h3>
        `;
        
        const criteriaLabels = {
            'criteria_1': '1. Ведущие синдромы заболевания',
            'criteria_2': '2. Эпидемиологические данные',
            'criteria_3': '3. Характерные объективные данные',
            'criteria_4': '4. Обоснование диагноза',
            'criteria_5': '5. План диагностики',
            'criteria_6': '6. План лечения'
        };
        
        for (const [key, criteria] of Object.entries(result.criteria_evaluation)) {
            const label = criteriaLabels[key] || key;
            const criteriaScore = criteria.score || 0;
            const isComplete = criteria.is_complete || false;
            
            let criteriaScoreClass = 'poor';
            if (criteriaScore >= 80) criteriaScoreClass = 'excellent';
            else if (criteriaScore >= 60) criteriaScoreClass = 'good';
            else if (criteriaScore >= 40) criteriaScoreClass = 'average';
            
            html += `
                <div class="criterion-card ${isComplete ? 'complete' : 'incomplete'}">
                    <div class="criterion-header">
                        <h4>${label}</h4>
                        <span class="criterion-score ${criteriaScoreClass}">${criteriaScore}/100</span>
                    </div>
                    <div class="criterion-feedback">
                        <p><strong>Отзыв:</strong> ${criteria.feedback || 'Нет отзыва'}</p>
                    </div>
            `;
            
            if (criteria.missing_points && criteria.missing_points.length > 0) {
                html += `
                    <div class="missing-points">
                        <strong>❌ Отсутствует в ответе:</strong>
                        <ul>
                            ${criteria.missing_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            if (criteria.incorrect_points && criteria.incorrect_points.length > 0) {
                html += `
                    <div class="incorrect-points">
                        <strong>⚠️ Указано неверно:</strong>
                        <ul>
                            ${criteria.incorrect_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            html += `</div>`;
        }
        
        html += `</div>`;
    }

    // Сильные стороны
    if (result.strengths && result.strengths.length > 0) {
        html += `
            <div class="feedback-section">
                <h3>✅ Сильные стороны</h3>
                <ul>
                    ${result.strengths.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Рекомендации
    if (result.recommendations && result.recommendations.length > 0) {
        html += `
            <div class="feedback-section">
                <h3>💡 Рекомендации для улучшения</h3>
                <ul>
                    ${result.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    } else if (result.weaknesses && result.weaknesses.length > 0) {
        html += `
            <div class="feedback-section">
                <h3>💡 Что нужно улучшить</h3>
                <ul>
                    ${result.weaknesses.map(w => `<li>${w}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    resultsContent.innerHTML = html;
}

