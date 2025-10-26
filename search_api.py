import os
import re
import time
import random
import json # Добавляем для более удобного логирования JSON
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
    и для демонстрации логики поиска.
    """
    results = []
    # Для отладки используем фиксированный список сайтов и немного меняем цены
    SOURCES = ["pop-music.ru", "muz-torg.ru", "pro-sound.ru", "audiomania.ru"]
    BASE_PRICE = 20000 
    
    for i in range(1, REQUIRED_RESULTS + 1):
        # Имитируем небольшое ранжирование
        rank = 1 if i % 5 == 0 else random.randint(2, 5)

        # Случайное изменение цены
        price_offset = random.randint(-2000, 3000)
        price = BASE_PRICE + price_offset

        source = random.choice(SOURCES)
        
        results.append({
            "title": f"Микрофон Shure SM58 BETA (Mock #{i}) от {query}",
            "snippet": f"Профессиональный динамический микрофон. Отличное качество звука для живых выступлений. Предложение с сайта {source}.",
            "uri": f"https://www.{source}/product/shure-mock-{i}",
            "source": source,
            "price": price,
            "rank": rank,
            "currency": "₽"
        })
    
    # Сортируем по цене, как требует логика
    results.sort(key=lambda x: x['price'])
    return results

def scrape_product_page(url: str) -> dict or None:
    """
    Имитирует скрапинг отдельной страницы товара. 
    В реальном приложении здесь будет логика парсинга HTML.
    """
    # Имитируем задержку
    time.sleep(random.uniform(0.1, 0.5)) 
    return None # Не возвращаем ничего, т.к. generate_mock_results уже сформировал данные

# ==============================================================================
# ОСНОВНАЯ ЛОГИКА ПОИСКА (ДВУХЭТАПНАЯ ИМИТАЦИЯ)
# ==============================================================================

def two_stage_search(query: str) -> tuple[list[dict], int]:
    """
    Имитация двухэтапного поиска:
    1. Получение ссылок (имитируется)
    2. Скрапинг страниц (имитируется)
    """
    print(f"[{time.strftime('%H:%M:%S')}] [STAGE 1] Имитация поиска ссылок для: '{query}'...")
    
    # 1. Имитация получения ссылок
    # В реальном приложении: links = get_search_links(query)
    # Для отладки мы просто генерируем мок-данные
    
    # 2. Имитация скрапинга
    print(f"[{time.strftime('%H:%M:%S')}] [STAGE 2] Имитация сбора данных...")
    
    # Генерируем все 20 мок-результатов сразу
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
    Ожидает JSON-тело с полем 'queries' (массив строк), как требует фронтенд.
    """
    
    # ******************************************************************************
    # ОТЛАДОЧНАЯ ЛОГИКА: УНИКАЛЬНАЯ МЕТКА ДЛЯ ПОДТВЕРЖДЕНИЯ ЗАПУСКА СКРИПТА
    # ******************************************************************************
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{current_time}] --- БЭКЕНД АКТИВЕН (search_api.py) ---")


    if not request.json or 'queries' not in request.json or not isinstance(request.json['queries'], list):
        print(f"[{current_time}] ОШИБКА 400: Неверный формат запроса. Получено: {request.json}")
        return jsonify({"error": "Требуется JSON-тело с полем 'queries' (массив строк). Фронтенд check."}), 400

    queries = request.json['queries']
    
    # Используем первый запрос из массива (наиболее точный или основной) 
    # для логики двухэтапного поиска.
    main_query = queries[0] if queries else "generic audio equipment" 

    # ******************************************************************************
    # ОТЛАДОЧНАЯ ЛОГИКА: ВЫВОД ПОЛУЧЕННЫХ ДАННЫХ
    # ******************************************************************************
    print(f"[{current_time}] Принят запрос. Основной query: '{main_query}'")
    try:
        # Пытаемся красиво вывести весь полученный JSON
        print(f"[{current_time}] JSON-тело: {json.dumps(request.json, indent=2)}")
    except Exception as e:
        print(f"[{current_time}] Ошибка при парсинге JSON для вывода: {e}")

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
    return jsonify({"status": "ok", "service": "psp-search-backend (Two-Stage Scraping Mock)"})

if __name__ == '__main__':
    # Если вы запускаете этот файл напрямую, Flask будет запущен
    print("Запуск Flask-сервера...")
    app.run(debug=True, port=5000)
