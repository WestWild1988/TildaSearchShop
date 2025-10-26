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
    и сортировки, как того требует фронтенд.
    """
    results = []
    base_product_name = query.replace(' ', '-').title()
    base_source_url = f"https://mock-shop-{random.randint(1, 9)}.ru"
    
    # Генерируем 20 уникальных результатов
    for i in range(1, REQUIRED_RESULTS + 1):
        # Генерируем уникальную цену, чтобы обеспечить разнообразие для сортировки
        base_price = random.randint(30000, 150000)
        price_variation = random.randint(-5000, 5000)
        price = base_price + price_variation
        
        # Определяем ранг. Для мока используем i == 1 для "лучшего"
        rank = 1 if i == 1 else i 
        
        # Генерируем реалистичный сниппет
        snippet = f"Профессиональный микрофон {base_product_name} с кардиоидной диаграммой. Идеален для студийной записи и живых выступлений. Гарантия 1 год. Скидка -{random.randint(5, 15)}%!"
        
        results.append({
            "title": f"Купить {base_product_name} — Цена {price}₽",
            "snippet": snippet,
            "uri": f"{base_source_url}/product/{base_product_name.lower()}-{i}",
            "source": urlparse(base_source_url).netloc,
            "price": price,
            "rank": rank
        })
    
    # Перемешиваем результаты, чтобы проверить сортировку на фронтенде
    random.shuffle(results)
    
    # Обеспечиваем, что первый результат с rank=1 всегда присутствует
    # (хотя он мог быть перемешан, но его price остается)
    
    return results

# ==============================================================================
# ЭТАП 2: ДВУХЭТАПНЫЙ ПОИСК (УПРОЩЕННАЯ РЕАЛИЗАЦИЯ)
# ==============================================================================

def two_stage_search(query: str) -> tuple[list[dict], int]:
    """
    Имитация двухэтапного поиска:
    1. Получение ссылок (имитация).
    2. Скрапинг страниц (имитация генерации мок-результатов).
    """
    print(f"[{time.strftime('%H:%M:%S')}] Имитация Stage 1: Получение ссылок для запроса: '{query}'")
    # Имитация задержки поиска
    time.sleep(random.uniform(0.5, 1.5)) 
    
    # В реальном приложении здесь был бы вызов get_search_links()
    
    # Имитируем генерацию 20 уникальных результатов
    final_results = generate_mock_results(query)
    
    print(f"[{time.strftime('%H:%M:%S')}] Имитация Stage 2: Скрапинг завершен. Найдено {len(final_results)} результатов.")
        
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
    Ожидает JSON-тело с полем 'queries' (массив строк), как требует фронтенд.
    """
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Проверяем наличие 'queries'
    if not request.json or 'queries' not in request.json or not isinstance(request.json['queries'], list):
        print(f"[{time.strftime('%H:%M:%S')}] ОШИБКА 400: Неверный формат запроса. Ожидается 'queries' (массив строк). Получено: {request.json}")
        return jsonify({"error": "Требуется JSON-тело с полем 'queries' (массив строк)."}, 400)

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
    return jsonify({"status": "ok", "service": "psp-search-backend (Two-Stage Scraping Mock)"}), 200

if __name__ == '__main__':
    # Эта часть не используется в Canvas, но полезна для локального тестирования
    app.run(debug=True, port=5000)
