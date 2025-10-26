from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin # Импортируем cross_origin
from tildasearchshop.search_logic import run_search

app = Flask(__name__)
# Инициализация CORS для ВСЕГО приложения (этот способ надежнее для OPTIONS)
CORS(app) 

# --- МАРШРУТ 1: ГЛАВНАЯ СТРАНИЦА (ДЛЯ ТЕСТИРОВАНИЯ АКТИВНОСТИ)
# Этот маршрут позволяет нам убедиться, что веб-запрос по адресу https://tildasearchshop.onrender.com/
# успешно доходит до сервера и Flask-приложение запущено.
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
            h1 { color: #4CAF50; } /* Зеленый цвет для подтверждения */
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
# Обрабатывает запросы поиска, отправляемые из Canvas
@app.route('/api/search', methods=['POST'])
# Теперь CORS явно включен для этого маршрута, включая OPTIONS
# Это должно решить проблему "Failed to fetch"
@cross_origin()
def search():
    """
    Принимает JSON с полем 'query' и возвращает результаты поиска.
    """
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
