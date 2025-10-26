from flask import Flask, request, jsonify, send_file
from flask_cors import CORS 
import random
import time
import re
from requests.exceptions import RequestException

# Инициализация приложения Flask
app = Flask(__name__)
CORS(app) 

# --- КОНСТАНТЫ И ФУНКЦИИ ДЛЯ ИМИТАЦИИ ПАРСИНГА И ЛОГИКИ (Требование 2.3) ---

def extract_price(text: str) -> float:
    """
    Имитирует извлечение цены. 
    Теперь используется для генерации реалистичных цен, т.к. реальный парсинг невозможен.
    """
    # Генерация цены от 15 000 до 25 000 + случайный сдвиг
    return random.randint(15000, 25000) + random.randint(0, 5000)

def generate_mock_results(query: str, count: int = 20) -> list:
    """
    Генерирует 20 (Требование 2.4.a) структурированных Mock-результатов с имитацией парсинга
    и устанавливает ранг 1 для лучшего предложения (Требование 4.4).
    """
    print(f"ЛОГ БЭКЕНДА: Имитация запроса к внешнему источнику для: {query}")
    time.sleep(1) # Имитация задержки сети и парсинга

    final_results = []
    source_options = ["Яндекс.Маркет", "Ozon", "MusicStore.ru", "Avito Pro", "ProStudioShop"]
    base_price = random.randint(10000, 60000)

    for i in range(count):
        # Генерируем данные с учетом реальных полей, ожидаемых фронтендом (Требование 2.3)
        # Имитируем разброс цен
        price = base_price + (random.randint(1, 10) * 1000) - (500 * (i % 3))
        
        final_results.append({
            "id": i + 1,
            "title": f"Оборудование '{query}' — Модель Pro V{i + 1}",
            "snippet": f"Краткое описание товара от источника. Отлично подходит для студийной и сценической работы. Гарантия {random.randint(6, 24)} месяцев.",
            "uri": f"https://example.com/item/{i + 1}",
            "source": random.choice(source_options),
            "price": max(5000, price), # Гарантируем минимальную цену
            "rank": 0,
        })

    # --- СОРТИРОВКА И УСТАНОВКА РАНГА (Требование 2.3) ---
    # Бэкенд возвращает отсортированные данные по возрастанию цены
    final_results.sort(key=lambda x: x['price'])
    
    if final_results:
        # Устанавливаем ранг 1 для самого дешевого
        final_results[0]['rank'] = 1 

    print(f"ЛОГ БЭКЕНДА: Возвращается {len(final_results)} отсортированных результатов. Лучшая цена: {final_results[0]['price']} руб.")
    return final_results

# --- МАРШРУТ 1: ГЛАВНАЯ СТРАНИЦА (ОТДАЧА ФРОНТЕНДА) ---
@app.route('/', methods=['GET'])
def serve_frontend():
    # Отдаем фронтенд (index.html), который должен находиться рядом
    # Это позволяет пользователю увидеть интерфейс при прямом обращении к домену
    try:
        return send_file('index.html')
    except FileNotFoundError:
        return "Ошибка: Файл index.html не найден. Пожалуйста, убедитесь, что он находится в корневой папке.", 500

# --- МАРШРУТ 2: API ПОИСКА (ОСНОВНАЯ ФУНКЦИЯ) ---
@app.route('/api/search', methods=['POST']) 
def search_catalog():
    start_time = time.time()
    
    try:
        # 1. Обработка входящего JSON
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Не удалось распарсить JSON-тело запроса. Ожидается JSON."}), 400

    # 2. Извлекаем массив 'queries', который отправляет фронтенд (Требование 2.2.a)
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    # Используем первый запрос из массива для выполнения поиска (заглушка)
    query_to_use = queries[0]
    
    # 3. Вызываем функцию, имитирующую поиск и ранжирование
    try:
        results = generate_mock_results(query_to_use)
    except RequestException as e:
        # Обработка ошибок, связанных с внешними запросами (например, таймаут)
        print(f"ЛОГ БЭКЕНДА: Ошибка внешнего запроса: {e}")
        return jsonify({"status": "error", "message": "Ошибка подключения к внешнему источнику поиска."}), 500


    # 4. Возвращаем успешный ответ
    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    
    return jsonify({
        "status": "success",
        "query": query_to_use,
        "execution_time_seconds": execution_time,
        "results_count": len(results),
        "results": results # Отсортированные и ранжированные данные
    }), 200

# --- ЗАПУСК ДЛЯ ЛОКАЛЬНОГО ТЕСТИРОВАНИЯ ---
if __name__ == '__main__':
    # Flask будет прослушивать порт 5000. В продакшене (Render) это делает Gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)
