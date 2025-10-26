from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin 
# У вас в последних версиях не было импорта tildasearchshop.search_logic, 
# я добавил простой placeholder, чтобы код оставался рабочим.
# from tildasearchshop.search_logic import run_search 

app = Flask(__name__)
# Инициализация CORS для ВСЕГО приложения (этот способ надежнее для OPTIONS)
CORS(app) 

# --- МАРШРУТ 1: ГЛАВНАЯ СТРАНИЦА (ДЛЯ ТЕСТИРОВАНИЯ АКТИВНОСТИ)
@app.route('/', methods=['GET'])
def index():
    # Возвращаем простой HTML, который подтверждает, что сервер работает
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <title>TildaSearchShop API Status</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            h1 { color: #4CAF50; } 
        </style>
    </head>
    <body>
        <h1>TildaSearchShop API Активен!</h1>
        <p>Flask-приложение успешно запущено.</p>
        <p>Отправьте POST-запрос с JSON-телом {"query": "ваш запрос"} на адрес:</p>
        <code style="background-color: #f0f0f0; padding: 5px 10px; border-radius: 5px;">/api/search</code>
    </body>
    </html>
    """, 200

# --- МАРШРУТ 2: API ПОИСКА (ОСНОВНАЯ ФУНКЦИЯ)
@app.route('/api/search', methods=['GET', 'POST', 'OPTIONS']) 
def search_catalog():
    # Если это GET-запрос (пользователь открыл адрес в браузере), отдаем форму отладки
    if request.method == 'GET':
        return """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <title>Тестирование TildaSearchShop API</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                /* Стилизация для мобильных устройств и лучшей читаемости */
                body {
                    font-family: 'Inter', sans-serif;
                    background-color: #f3f4f6;
                }
                .container {
                    max-width: 600px;
                    margin: 40px auto;
                    padding: 20px;
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                }
                .status-box {
                    padding: 10px;
                    border-radius: 8px;
                    margin-top: 15px;
                    font-weight: 600;
                    text-align: center;
                }
                .status-success {
                    background-color: #d1fae5;
                    color: #065f46;
                }
                .status-error {
                    background-color: #fee2e2;
                    color: #991b1b;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2 class="text-2xl font-bold mb-4 text-center text-gray-800">TildaSearchShop API Тест</h2>
                <p class="text-gray-600 mb-6 text-center">Отправка POST-запроса на <code>/api/search</code></p>
                
                <div class="mb-4">
                    <label for="queryInput" class="block text-sm font-medium text-gray-700 mb-1">Поисковый запрос (JSON: {"query": "..."})</label>
                    <input type="text" id="queryInput" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" value="тестовый запрос для успеха">
                </div>
                
                <button id="sendButton" class="w-full bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700 transition duration-150 ease-in-out font-semibold">
                    Отправить POST-запрос к API
                </button>

                <div id="loading" class="mt-4 text-center hidden">
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-600 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Ожидание ответа...
                </div>
                
                <div id="responseStatus" class="status-box hidden mt-4"></div>
                
                <div class="mt-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Ответ Сервера (JSON)</h3>
                    <pre id="responseJson" class="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto text-gray-700 max-h-60"></pre>
                </div>
            </div>

            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    const sendButton = document.getElementById('sendButton');
                    const queryInput = document.getElementById('queryInput');
                    const responseStatus = document.getElementById('responseStatus');
                    const responseJson = document.getElementById('responseJson');
                    const loading = document.getElementById('loading');
                    
                    const apiUrl = 'https://tildasearchshop.onrender.com/api/search'; // Используем полный абсолютный URL
                    
                    sendButton.addEventListener('click', async () => {
                        const query = queryInput.value.trim();
                        if (!query) {
                            alert('Введите запрос для тестирования!');
                            return;
                        }

                        // Сброс и индикация загрузки
                        responseStatus.classList.add('hidden');
                        responseJson.textContent = 'Ожидание...';
                        loading.classList.remove('hidden');
                        sendButton.disabled = true;

                        try {
                            // Формируем тело запроса
                            const payload = JSON.stringify({ query: query });
                            
                            // Отправка запроса с полным URL
                            const response = await fetch(apiUrl, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: payload
                            });

                            const data = await response.json();
                            
                            // Отображение статуса
                            responseStatus.textContent = `Статус: ${response.status} ${response.statusText}`;
                            
                            if (response.ok) {
                                responseStatus.className = 'status-box status-success';
                            } else {
                                responseStatus.className = 'status-box status-error';
                            }
                            
                            // Отображение JSON-ответа
                            responseJson.textContent = JSON.stringify(data, null, 2);
                            responseStatus.classList.remove('hidden');

                        } catch (error) {
                            console.error('Ошибка при выполнении запроса:', error);
                            responseStatus.textContent = `Ошибка: Failed to fetch - Проверьте, активен ли сервер Render!`;
                            responseStatus.className = 'status-box status-error';
                            responseJson.textContent = `Error: ${error.message}\nПроверьте консоль для деталей.`;
                            responseStatus.classList.remove('hidden');
                        } finally {
                            loading.classList.add('hidden');
                            sendButton.disabled = false;
                        }
                    });
                });
            </script>
        </body>
        </html>
        """, 200

    # Если это POST-запрос, то обрабатываем его как API-вызов
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            # 400 Bad Request: Отсутствует поисковый запрос
            return jsonify({"error": "Поле 'query' обязательно для заполнения."}), 400

        # ВРЕМЕННЫЙ ОТВЕТ: возвращаем тестовые данные, пока не будет реализована логика поиска
        results = [
            {"id": 1, "title": f"Тестовый результат 1 для: {query}", "link": "#"},
            {"id": 2, "title": f"Тестовый результат 2 для: {query}", "link": "#"}
        ]
        
        return jsonify({
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": results
        }), 200

    except Exception as e:
        # Обработка непредвиденных ошибок
        print(f"Ошибка при обработке запроса: {e}")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500

if __name__ == '__main__':
    # Запуск для локального тестирования
    app.run(host='0.0.0.0', port=5000)
