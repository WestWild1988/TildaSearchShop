from flask import Flask, request, jsonify
# Импортируем логику поиска, которую мы будем разрабатывать
from tilda_search import run_search 

app = Flask(__name__)

# --- МАРШРУТ 1: ГЛАВНАЯ СТРАНИЦА (ДЛЯ ТЕСТИРОВАНИЯ АКТИВНОСТИ) ---
# Этот маршрут будет отвечать на GET-запросы по адресу https://tildasearchshop.onrender.com/
@app.route('/', methods=['GET'])
def index():
    # Возвращаем простой HTML, который подтверждает, что сервер работает
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
# Этот маршрут обрабатывает запросы поиска, отправленные из Canvas
@app.route('/api/search', methods=['POST'])
def search_catalog():
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            # 400 Bad Request: Отсутствует поисковый запрос
            return jsonify({"error": "Поле 'query' обязательно для заполнения."}), 400

        # Вызов реальной функции поиска из tilda_search.py
        # В данный момент эта функция возвращает тестовые данные, если query == "тестовый запрос для успеха"
        results = run_search(query) 
        
        if results:
            # 200 OK: Успешный ответ с найденными товарами
            return jsonify({"query": query, "results": results}), 200
        else:
            # 404 Not Found: Ничего не найдено
            return jsonify({"error": f"Ничего не найдено в каталоге по запросу: {query}"}), 404

    except Exception as e:
        # Обработка непредвиденных ошибок сервера
        # print(f"Критическая ошибка: {e}") 
        return jsonify({"error": "Внутренняя ошибка сервера", "details": str(e)}), 500
