from flask import Flask, request, jsonify
from flask_cors import CORS # Импорт модуля CORS

app = Flask(__name__)
# Инициализация CORS для разрешения запросов со всех доменов (по умолчанию)
CORS(app) 

# Тестовая функция-заглушка для имитации поиска
def run_search(query):
    # Если запрос "тестовый запрос для успеха", возвращаем тестовые данные
    if query and "тестовый запрос для успеха" in query.lower():
        return [
            {"name": "Тестовый товар 1", "price": 1000},
            {"name": "Тестовый товар 2", "price": 2500},
            {"name": "Тестовый товар 3", "price": 500}
        ]
    # В противном случае возвращаем пустой список или сообщение об ошибке
    return []

@app.route('/', methods=['GET'])
def index():
    return """
    <div style="text-align: center; padding: 50px; background-color: #e6fffa; border-radius: 10px; border: 2px solid #38b2ac;">
        <h1 style="color: #38b2ac;">TildaSearchShop API Активен!</h1>
        <p style="color: #4a5568;">Flask-приложение успешно запущено.</p>
        <p style="color: #4a5568;">Отправьте <b>POST-запрос</b> с JSON-телом {"query": "ваш запрос"} на адрес:</p>
        <code style="background-color: #f7fafc; padding: 5px 10px; border-radius: 5px; color: #e53e3e;">/api/search</code>
    </div>
    """, 200

@app.route('/api/search', methods=['POST'])
def search():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # Вызываем функцию поиска
    results = run_search(query)
    
    # Возвращаем результаты в формате JSON
    return jsonify({"query": query, "results": results})

if __name__ == '__main__':
    # В среде Render это запускает Gunicorn
    app.run(host='0.0.0.0', port=5000)
