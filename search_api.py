from flask import Flask, request, jsonify

app = Flask(__name__)

# --- ВРЕМЕННАЯ ФУНКЦИЯ-ЗАГЛУШКА (run_search) ---
# Эта функция должна быть в отдельном файле, но временно помещена сюда,
# чтобы Gunicorn не падал при запуске на Render.
def run_search(query: str) -> list[dict]:
    """Тестовая заглушка для проверки маршрутов."""
    if query.lower() == "тестовый запрос для успеха":
        return [
            {"name": "Тестовый товар 1", "price": 1000},
            {"name": "Тестовый товар 2", "price": 2500}
        ]
    return []

# --- МАРШРУТ 1: ГЛАВНАЯ СТРАНИЦА (ДЛЯ ТЕСТИРОВАНИЯ АКТИВНОСТИ) ---
# Этот маршрут будет отвечать на GET-запросы по адресу https://tildasearchshop.onrender.com/
@app.route('/', methods=['GET'])
def index():
    # Возвращаем простое сообщение, которое подтверждает, что сервер работает
    return """
        <!DOCTYPE html>
        <html>
        <head><title>API Status</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
            <h1 style="color: #4CAF50;">TildaSearchShop API Активен!</h1>
            <p>Flask-приложение успешно запущено.</p>
            <p>Отправьте POST-запрос с JSON-телом {"query": "ваш запрос"} на адрес:</p>
            <code style="background-color: #f0f0f0; padding: 5px 10px; border-radius: 5px;">/api/search</code>
        </body>
        </html>
    """, 200

# --- МАРШРУТ 2: API ПОИСКА (ОСНОВНАЯ ФУНКЦИЯ) ---
@app.route('/api/search', methods=['POST'])
def search_catalog():
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({"error": "Поле 'query' обязательно для заполнения."}), 400

        # Вызов временной функции-заглушки run_search
        results = run_search(query) 
        
        if results:
            return jsonify({"query": query, "results": results}), 200
        else:
            return jsonify({"error": f"Ничего не найдено в каталоге по запросу: {query}"}), 404

    except Exception as e:
        return jsonify({"error": "Внутренняя ошибка сервера", "details": str(e)}), 500
