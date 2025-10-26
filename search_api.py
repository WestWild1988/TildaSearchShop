from flask import Flask, request, jsonify
import random
import requests # Для имитации запроса к внешнему ресурсу (например, Яндексу)
from bs4 import BeautifulSoup # Для имитации парсинга
import time # Для имитации задержки сети

# Инициализация приложения Flask
app = Flask(__name__)

# --- ФУНКЦИЯ ДЛЯ ИМИТАЦИИ ПАРСИНГА ЯНДЕКС (Заменит generate_mock_results) ---
def perform_yandex_search(query):
    """
    Имитирует выполнение поиска через Requests и BeautifulSoup.
    ВРЕМЕННО возвращает структурированный Mock-массив,
    чтобы соответствовать требованиям фронтенда, пока не будет реализован реальный парсинг.
    """
    print(f"Выполнение имитации запроса к внешнему источнику для: {query}")
    
    # Имитация сетевой задержки (для реалистичности)
    time.sleep(0.5) 

    # --- СЕКЦИЯ, КОТОРУЮ НЕОБХОДИМО ЗАМЕНИТЬ РЕАЛЬНОЙ ЛОГИКОЙ ПАРСИНГА ---
    
    mockData = []
    basePrice = random.randint(10000, 60000) 

    for i in range(20):
        # Генерируем данные с учетом реальных полей, ожидаемых фронтендом
        price = basePrice + (1000 * i) - (500 * (i % 2))
        rank = 1 if i == 0 else random.randint(2, 6)
        
        mockData.append({
            "id": i + 1,
            "title": f"[ЯНДЕКС ИМИТАЦИЯ] {query} — Результат №{i + 1}",
            "snippet": f"Это краткое описание имитирует результат, полученный парсингом Яндекс. Мы нашли отличные цены на {query}.",
            "uri": f"https://mock-yandex.com/item/{i + 1}",
            "source": f"Яндекс.Маркет Имитация {chr(65 + i // 5)}", 
            "price": max(100, price), 
            "rank": rank 
        })
    
    # Сортируем по цене, как требует фронтенд
    mockData.sort(key=lambda x: x['price'])
    return mockData

# --- МАРШРУТ API ---
@app.route('/api/search', methods=['POST'])
def search_catalog():
    # 1. Обработка входящего JSON
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Не удалось распарсить JSON-тело запроса."}), 400

    # 2. Извлекаем массив 'queries', который отправляет фронтенд
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    # Используем первый запрос из массива для выполнения поиска
    query_to_use = queries[0]
    
    # Вызываем функцию, имитирующую поиск
    results = perform_yandex_search(query_to_use)

    # 3. Возвращаем успешный ответ
    return jsonify({
        "status": "success",
        "query_used": query_to_use,
        "results_count": len(results),
        "results": results 
    }), 200

# Для локального запуска
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
