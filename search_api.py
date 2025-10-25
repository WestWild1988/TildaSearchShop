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
    и фильтрации на основе одного ключевого запроса.
    """
    # Гарантируем, что цена будет в диапазоне, который может быть обработан
    # ползунками фронтенда (до ~1000 * 1000 = 1,000,000 руб.)
    base_price = random.randint(15000, 35000)
    
    mock_data = []
    
    # Генерируем 20 результатов
    for i in range(REQUIRED_RESULTS):
        # Цена с небольшим разбросом
        price_offset = random.randint(-5000, 15000)
        price = max(1000, base_price + price_offset + (i * 100))
        
        # Различные источники
        sources = ['ozon.ru', 'market.yandex.ru', 'pop-music.ru', 'muzmarket.ru']
        source = sources[i % len(sources)]
        
        # Rank: назначаем 1 для первого результата, чтобы проверить бейдж на фронте
        rank = 1 if i == 0 else random.choice([2, 3, 4, 5])
        
        item = {
            "title": f"Микрофон {query.capitalize()} Pro X {100 + i}",
            "snippet": f"Профессиональная модель для студийной записи. Отличный выбор для {query}. Гарантия 1 год.",
            "uri": f"https://{source}/product/{i+1}",
            "source": source,
            "price": price,
            "rank": rank,
        }
        mock_data.append(item)
    
    # Сортируем по цене для соответствия правилам
    mock_data.sort(key=lambda x: x['price'])
    
    # Обновляем rank после сортировки, чтобы самый дешевый был rank 1
    for i in range(len(mock_data)):
        # Назначаем Rank 1 самому дешевому товару
        mock_data[i]['rank'] = 1 if i == 0 else random.randint(2, 5)

    return mock_data

def get_search_links(base_query: str) -> list[str]:
    """
    Имитирует вызов внешнего поисковика (Яндекс/Google) для получения 
    списка релевантных ссылок.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Имитация: Получение ссылок для '{base_query}'")
    
    # Имитируем задержку
    time.sleep(random.uniform(0.5, 1.5))
    
    # В реальном приложении здесь будет логика вызова поискового API.
    return []

# ==============================================================================
# ЭТАП 2: ДВУХЭТАПНЫЙ ПОИСК И ГЕНЕРАЦИЯ МОК-ДАННЫХ
# ==============================================================================

def two_stage_search(query: str) -> tuple[list, int]:
    """
    Имитирует двухэтапный процесс: 
    1. Получение ссылок (сейчас игнорируется).
    2. Глубокий скрапинг (сейчас имитируется генерацией данных).
    
    Возвращает 20 мок-результатов.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Запуск двухэтапного поиска для '{query}'")
    
    # 1. Имитация Этапа 1 (Получение ссылок)
    # links = get_search_links(query) 
    
    # 2. Имитация Этапа 2 (Глубокий скрапинг / Генерация данных)
    # Используем мок-генератор, чтобы гарантировать 20 результатов
    final_results = generate_mock_results(query)
            
    # 3. Возвращаем результат
    if not final_results:
        # Это должно быть невозможно с мок-генератором, но для надежности
        return {"error": f"Ничего не найдено по запросу: {query}"}, 404
            
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
        print(f"[{time.strftime('%H:%M:%S')}] ОШИБКА 400: Неверный формат запроса. Получено: {request.json}")
        return jsonify({"error": "Требуется JSON-тело с полем 'queries' (массив строк)."}), 400

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
    # ВНИМАНИЕ: Для продакшена используйте Gunicorn или другой WSGI-сервер
    # Flask-сервер используется только для локальной разработки
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
