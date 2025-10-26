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

# Таймаут для каждого запроса на скрапинг отдельной страницы (для имитации)
SCRAPE_TIMEOUT = 5 
# Нам нужно 20 результатов (4 страницы по 5)
REQUIRED_RESULTS = 20 
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ==============================================================================
# УТИЛИТЫ ИМИТАЦИИ СКАНИРОВАНИЯ
# ==============================================================================

def generate_mock_results(query: str) -> list[dict]:
    """
    Генерирует 20 уникальных, реалистичных мок-результатов для пагинации
    и сортировки. Эта функция имитирует результат двухэтапного поиска.
    
    :param query: Основной поисковый запрос.
    :return: Список объектов-результатов.
    """
    results = []
    
    # Имитируем разные магазины
    sources = [
        "pop-music.ru", "muztorg.ru", "djdome.ru", "sindor.pro", 
        "audiomania.ru", "prodevice.ru", "market-pro.ru", "a&t-trade.ru"
    ]
    
    # Имитируем 20 результатов
    for i in range(REQUIRED_RESULTS):
        # Генерируем уникальную цену, чтобы обеспечить хорошую сортировку
        # Цены в рублях (₽), округлены до сотен
        price = random.randint(15000, 150000) * (1 + (i % 5) * 0.01)
        price = int(round(price, -2)) 
        
        # Имитация названия товара
        product_name_part = query.replace(' equipment', '').strip()
        brand = random.choice(["Shure", "Sennheiser", "AKG", "Neumann", "Rode"])
        model = f"{brand} {product_name_part} Model V{random.randint(1, 10)}{random.choice(['A', 'B', 'C'])}"
        
        # Имитация сниппета
        snippet = f"Профессиональный динамический {product_name_part.lower()} для студийной и сценической работы. В наличии. Доставка от {random.randint(2, 7)} дней."
        
        # Имитация URI и Source
        source = random.choice(sources)
        uri = f"https://www.{source}/product/{i+1}/{model.replace(' ', '-').lower()}"
        
        # Имитация ранга (для выделения лучших)
        rank = 1 if i == 0 else random.randint(2, 10)
        
        results.append({
            "title": model,
            "snippet": snippet,
            "uri": uri,
            "source": source,
            "price": price,
            "rank": rank
        })
    
    # Мок-данные возвращаются несортированными, 
    # сортировка будет выполняться на фронтенде согласно правилам.
    return results

def two_stage_search(query: str) -> tuple[list[dict], int]:
    """
    Имитирует основную логику двухэтапного поиска (Stage I & II).
    В реальном приложении здесь будет логика вызова поискового API и скрапинга.
    
    :param query: Основной поисковый запрос (берется первый из массива 'queries').
    :return: Список результатов и статус-код.
    """
    # Имитация задержки API
    time.sleep(random.uniform(1.0, 3.0)) 
    
    if "ошибка" in query.lower():
        # Имитация ошибки на стороне бэкенда
        return {"error": "Имитация внутренней ошибки сервера (500)."}, 500
        
    # Возвращаем мок-результаты
    results = generate_mock_results(query)
    
    if not results:
        return {"error": f"Ничего не найдено после двухэтапного поиска по запросу: {query}"}, 404
            
    return results, 200

# ==============================================================================
# FLASK ROUTE
# ==============================================================================

@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """
    Основная конечная точка для приема поисковых запросов.
    Ожидает JSON-тело с полем 'queries' (массив строк), как требует фронтенд.
    """
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Теперь проверяем наличие 'queries'
    if not request.json or 'queries' not in request.json or not isinstance(request.json['queries'], list):
        # Эта ошибка 400 должна быть возвращена, если фронтенд отправляет неверный формат
        error_message = "Требуется JSON-тело с полем 'queries' (массив строк)."
        print(f"[{time.strftime('%H:%M:%S')}] ОШИБКА 400: Неверный формат запроса. Детали: {error_message}")
        return jsonify({"error": error_message}), 400

    queries = request.json['queries']
    
    # Используем первый запрос из массива (наиболее точный или основной) 
    # для логики двухэтапного поиска.
    main_query = queries[0] if queries else "generic audio equipment" 

    print(f"[{time.strftime('%H:%M:%S')}] Принят запрос. Основной query: '{main_query}', весь массив: {queries}")

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
    return jsonify({"status": "ok", "service": "psp-search-backend (Mock Two-Stage Scraping)"}), 200


if __name__ == '__main__':
    # При запуске локально, используем стандартный порт 5000
    port = int(os.environ.get('PORT', 5000))
    # Включаем отладочный режим только для локальной разработки
    app.run(debug=True, host='0.0.0.0', port=port)
