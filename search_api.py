import os
import re
import time
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

# ==============================================================================
# НАСТРОЙКА FLASK
# ==============================================================================

app = Flask(__name__)
# Включаем CORS для всех доменов, чтобы фронтенд мог обращаться к API
CORS(app)

# ==============================================================================
# КОНСТАНТЫ
# ==============================================================================

# Таймаут для каждого запроса на скрапинг отдельной страницы
SCRAPE_TIMEOUT = 5 
# Ограничиваем количество скрапируемых ссылок для демонстрации
MAX_LINKS_TO_SCRAPE = 5 
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ==============================================================================
# УТИЛИТЫ ИМИТАЦИИ СКАНИРОВАНИЯ
# ==============================================================================

def generate_mock_results(query: str) -> list[dict]:
    """
    Генерирует 20 уникальных, реалистичных мок-результатов для пагинации.
    """
    base_title = query.replace(' (Eng. Equivalent)', '').strip()
    
    # Определяем базовую цену для ранжирования
    base_price = random.randint(10000, 30000)
    
    results = []
    
    for i in range(1, 21):
        # Создаем уникальный URI и Source
        source = f"site-{random.randint(1, 5)}.ru"
        uri = f"https://{source}/product/{base_title.lower().replace(' ', '-')}-{i}"
        
        # Генерируем цену с небольшим разбросом
        price_variation = random.uniform(0.8, 1.2)
        price = round(base_price * price_variation, -2) # Округляем до сотен
        
        # Определяем ранг. Лучший результат (rank 1) будет всегда первым 
        # после сортировки, так как у него самая низкая цена.
        rank = 0
        if i == 1:
            # Делаем первый результат самым дешевым
            price = min(base_price * 0.7, 9999) 
            rank = 1

        results.append({
            "title": f"{base_title} - Версия {i}",
            "snippet": f"Описание товара {base_title}. Отличный микрофон для студийной и сценической работы. В наличии на складе в Москве.",
            "uri": uri,
            "source": source,
            "price": price,
            "rank": rank,
            "debug_query": query # Для отладки
        })
    
    # Сортируем по цене, чтобы rank=1 всегда был самым дешевым
    results.sort(key=lambda x: x['price'])
    # Устанавливаем rank=1 для самого дешевого после сортировки
    if results:
        results[0]['rank'] = 1
        
    return results

# ==============================================================================
# ЭТАП 1 & 2: ИМИТАЦИЯ ДВУХЭТАПНОГО ПОИСКА
# ==============================================================================

def two_stage_search(query: str) -> tuple[list[dict], int]:
    """
    Имитирует двухэтапный поиск:
    1. Поиск ссылок по запросу.
    2. Сканирование (скрапинг) этих ссылок.
    
    Поскольку реальный скрапинг запрещен, используем генерацию мок-данных.
    Искусственная задержка удалена, поиск теперь мгновенный.
    """
    print(f"BACKEND: Имитация поиска по запросу: {query}")
    # time.sleep(1.5) # Имитация задержки на поиск - УДАЛЕНО
    
    # 1. Имитация получения ссылок
    # В реальном приложении здесь был бы вызов поискового API
    
    # 2. Имитация сканирования/получения данных
    final_results = generate_mock_results(query)
            
    # 3. Возвращаем результат
    if not final_results:
        return {"error": f"Ничего не найдено после двухэтапного поиска по запросу: {query}"}, 404
            
    return final_results, 200


# ==============================================================================
# FLASK ROUTE
# ==============================================================================

@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """
    Основная конечная точка для приема поисковых запросов.
    Ожидает JSON-тело с полем 'queries' (массив строк).
    """
    if not request.json or 'queries' not in request.json or not isinstance(request.json['queries'], list):
        return jsonify({"error": "Требуется JSON-тело с полем 'queries' (массив строк)."}), 400

    queries = request.json['queries']
    
    # Используем первый запрос из массива (наиболее точный или основной) 
    # для существующей функции two_stage_search.
    main_query = queries[0] if queries else "" 

    # 1. Выполняем логику двухэтапного поиска
    results, status_code = two_stage_search(main_query)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Добавляем маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return jsonify({"status": "ok", "service": "psp-search-backend (Mock-Scraping)"}), 200

if __name__ == '__main__':
    # Используем порт 5000 для работы в среде Canvas
    app.run(debug=True, port=5000)
