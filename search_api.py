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

SCRAPE_TIMEOUT = 5 
REQUIRED_RESULTS = 20 # Обязательно 20 для пагинации (4 страницы по 5)
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Данные для имитации
BRANDS = ["Shure", "Sennheiser", "Neumann", "Rode", "Audio-Technica"]
SOURCES = ["MusMarket.ru", "ProAudioStore.net", "SoundLab.online", "MuzTorg.biz", "DJGear.pro"]
BASE_PRICE_RU = 25000 # Базовая цена в рублях

# ==============================================================================
# ИМИТАЦИЯ ГЛУБОКОГО СКРАПИНГА
# ==============================================================================

def simulate_deep_scraping(index: int, query: str) -> dict:
    """
    Имитирует глубокий скрапинг страницы для получения одного, 
    полностью структурированного результата.
    
    Args:
        index: Индекс результата (от 0 до 19) для обеспечения уникальности.
        query: Основной поисковый запрос.
        
    Returns:
        Словарь с результатом или None в случае имитации ошибки.
    """
    # Имитируем небольшую задержку скрапинга
    time.sleep(random.uniform(0.05, 0.2)) 
    
    # 1. Формирование данных
    brand = BRANDS[index % len(BRANDS)]
    source_name = SOURCES[index % len(SOURCES)]
    
    # Генерация цены с небольшим разбросом
    price = max(10000, BASE_PRICE_RU + (index * 500) - random.randint(0, 5000))
    
    title = f"{brand} Профессиональный Микрофон PSS {100 + index} ({query.capitalize()})"
    
    # Гарантируем, что только самый дешевый товар получит rank 1
    # Это будет обработано после генерации всех 20 результатов в two_stage_search
    mock_rank = random.randint(2, 5)

    result = {
        "title": title,
        "snippet": f"Имитация: Глубокий анализ страницы {source_name}. Идеально подходит для {query}. Доступно 5 цветов.",
        "uri": f"https://{source_name}/product/id{index+1}",
        "source": source_name,
        "price": price,
        "rank": mock_rank, 
    }
    
    return result

# ==============================================================================
# ЭТАП 2: ДВУХЭТАПНЫЙ ПОИСК (ГЛАВНАЯ ФУНКЦИЯ)
# ==============================================================================

def two_stage_search(query: str) -> tuple[list, int]:
    """
    Имитирует двухэтапный процесс поиска с гарантией 20 результатов.
    """
    print(f"[{time.strftime('%H:%M:%S')}] БЭКЕНД: Запуск двухэтапного поиска для '{query}'")
    
    final_results = []
    
    # 1. Имитация Этапа 1 (Получение 20 "Ссылок")
    # В реальном коде здесь был бы вызов Яндекса/Гугла
    links_to_scrape = [f"link_{i}" for i in range(REQUIRED_RESULTS)]
    print(f"[{time.strftime('%H:%M:%S')}] БЭКЕНД: Имитация. Получено {len(links_to_scrape)} ссылок.")
    
    # 2. Имитация Этапа 2 (Глубокий скрапинг каждой ссылки)
    for i, _ in enumerate(links_to_scrape):
        product_data = simulate_deep_scraping(i, query)
        if product_data:
            final_results.append(product_data)
            
    # 3. Постобработка: Сортировка по цене и назначение Rank 1 самому дешевому
    final_results.sort(key=lambda x: x['price'])
    
    if final_results:
        # Назначаем Rank 1 самому дешевому товару
        final_results[0]['rank'] = 1
        print(f"[{time.strftime('%H:%M:%S')}] БЭКЕНД: Успешно сгенерировано {len(final_results)} результатов (Rank 1 назначен).")
    
    # 4. Возвращаем результат
    if not final_results:
        return {"error": f"Ничего не найдено по запросу: {query}"}, 404
            
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
        print(f"[{time.strftime('%H:%M:%S')}] БЭКЕНД: ОШИБКА 400: Неверный формат запроса. Получено: {request.json}")
        return jsonify({"error": "Требуется JSON-тело с полем 'queries' (массив строк)."}), 400

    queries = request.json['queries']
    
    # Используем первый запрос как основной
    main_query = queries[0] if queries else "generic audio equipment" 

    print(f"[{time.strftime('%H:%M:%S')}] БЭКЕНД: Принят запрос. Основной query: '{main_query}', весь массив: {queries}")

    # 1. Выполняем логику двухэтапного поиска
    results, status_code = two_stage_search(main_query)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    # Добавляем лог для проверки, что сервер запущен
    print(f"[{time.strftime('%H:%M:%S')}] БЭКЕНД: Проверка работоспособности (Health Check) выполнена.")
    return jsonify({"status": "ok", "service": "psp-search-backend (Simulated Scraper)"}), 200

if __name__ == '__main__':
    print("Flask App запущен. Используйте /api/search с методом POST.")
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
