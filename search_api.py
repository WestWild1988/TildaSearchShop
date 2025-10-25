import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urljoin, urlparse, quote_plus
from bs4 import BeautifulSoup

# Импортируем библиотеки для скрапинга и имитации API
import requests
import json 
from typing import List, Dict, Optional, Tuple

app = Flask(__name__)
CORS(app)

# ==============================================================================
# КОНФИГУРАЦИЯ
# ==============================================================================

# Максимальное количество результатов поиска в Google для анализа
MAX_GOOGLE_SEARCH_RESULTS = 10 

# ==============================================================================
# УРОВЕНЬ 1: ВИРТУАЛЬНЫЙ ПОИСК (ИМИТАЦИЯ GOOGLE/ЯНДЕКС)
# ==============================================================================

def search_google_for_urls(query: str) -> List[Dict[str, str]]:
    """
    Имитирует поиск Google и возвращает список релевантных URL (объектов).
    
    ПРИОРИТЕТ: Найти максимально релевантные ссылки, а не только на конкретных доменах.
    """
    print(f"DEBUG: Уровень 1: Поиск релевантных URL по запросу: {query}")
    
    # Формируем максимально релевантный запрос для инструмента Google Search
    search_query = f'музыкальное оборудование "{query}" купить цена'
    
    # **Заглушка для демонстрации логики:**
    # Имитируем, что Google API вернул нам результаты со всех доменов
    # Включаем заведомо плохие результаты (без цены, без картинки) для фильтрации
    mock_google_results = [
        {"uri": "https://www.pagesound.ru/microphones/shure-sm7b-best-price", "title": "Shure SM7B - PageSound (Отличные данные)"},
        {"uri": "https://www.pop-music.ru/product/shure-mv7-black-usb-xlr", "title": "Shure MV7 - POP-MUSIC (Тоже отличные данные)"},
        {"uri": "https://forum-audio-pro.ru/review/sm7b-vs-mv7", "title": "SM7B vs MV7 - Форум (Не магазин, должен отфильтроваться)"},
        {"uri": "https://www.baza-shop.ru/catalog/mixer/yamaha-mg10xu", "title": "Yamaha MG10XU - BAZA (Данные могут быть неполными)"},
        {"uri": "https://randomshop.com/product/bad-data", "title": "Товар без цены и картинки (Для демонстрации отсева)"},
        {"uri": "https://mus-express.ru/item/krk-rokit-5-g4", "title": "KRK Rokit 5 G4 - Mus-Express"},
    ]

    # В реальном приложении здесь был бы вызов инструмента Google Search API,
    # и мы бы обрабатывали его ответ.
    
    # В этой версии мы не фильтруем по доменам, просто берем все ссылки
    return mock_google_results[:MAX_GOOGLE_SEARCH_RESULTS]


# ==============================================================================
# УРОВЕНЬ 2: ЦЕЛЕВОЙ СКРАПИНГ И ОБРАБОТКА ДАННЫХ
# ==============================================================================

def scrape_product_details(url: str):
    """
    Выполняет точечный скрапинг конкретного товара по URL и проверяет
    наличие ключевых данных (Цена и URL изображения).
    """
    print(f"DEBUG: Скрапинг товара по URL: {url}")
    
    try:
        # Имитация HTTP-запроса
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Ошибка при доступе к товару {url}. Пропускаем.")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    domain = urlparse(url).netloc.replace('www.', '')
    
    # --- СИМУЛЯЦИЯ ПОЛУЧЕНИЯ ДАННЫХ ---
    # В реальном скрапинге здесь были бы точные селекторы для каждого поля.
    
    # 1. Title
    title_tag = soup.find(['h1', 'h2'], class_=re.compile(r'(product-title|item-title)'))
    title = title_tag.get_text(strip=True) if title_tag else "Название не найдено"

    # 2. Snippet (Описание)
    snippet_tag = soup.find('div', class_=re.compile(r'(product-description|description)'))
    snippet = snippet_tag.get_text(strip=True)[:150] + "..." if snippet_tag else "Описание недоступно."
    
    # --- КРИТИЧЕСКАЯ ЛОГИКА ФИЛЬТРАЦИИ ПО КАЧЕСТВУ ДАННЫХ ---

    # 3. Price (СИМУЛЯЦИЯ):
    # Используем логику для имитации разных результатов с разных "сайтов"
    if "randomshop" in domain or "forum-audio-pro" in domain:
        # Имитируем отсутствие цены на сайте-форуме или нерабочем магазине
        raw_price = None 
        price_value = 0
    elif "shure-sm7b" in url:
        raw_price = "65000 ₽"
        price_value = 65000
    elif "shure-mv7" in url:
        raw_price = "22000 ₽"
        price_value = 22000
    elif "yamaha-mg10xu" in url:
        raw_price = "35000 ₽"
        price_value = 35000
    else:
        raw_price = "50000 ₽" # Дефолтная цена
        price_value = 50000
    
    # 4. Image URL (СИМУЛЯЦИЯ):
    image_url = "https://placehold.co/150x150/00BCD4/FFFFFF?text=Product"
    if "bad-data" in url:
        # Имитируем отсутствие изображения
        image_url = None 
    
    # --- ФИЛЬТРАЦИЯ: ОТБРАСЫВАЕМ РЕЗУЛЬТАТЫ БЕЗ ЦЕНЫ И ИЗОБРАЖЕНИЯ ---
    
    if not raw_price or not image_url or "forum-audio-pro" in domain:
        print(f"DEBUG: Товар '{title}' отброшен: Неполные данные (Цена: {raw_price}, Изображение: {bool(image_url)}).")
        return None # Отбрасываем, если нет цены или картинки
    
    # Возвращаем структурированные данные с числовой ценой для сортировки
    return {
        "title": title,
        "snippet": snippet,
        "uri": url,
        "price_raw": raw_price,        # Строка для отображения
        "price_value": price_value,    # Число для сортировки
        "image_url": image_url,
        "source_domain": domain
    }

# ==============================================================================
# ГЛАВНАЯ ЛОГИКА
# ==============================================================================

def execute_multi_source_search(query: str):
    """
    Выполняет двухэтапный многоисточниковый поиск.
    """
    
    # 1. Уровень 1: Имитация поиска Google/Яндекс для получения релевантных ссылок
    target_results = search_google_for_urls(query)
    
    if not target_results:
        return {"error": f"Виртуальный поиск не нашел релевантных ссылок для '{query}'."}, 404

    preliminary_results = []
    
    # 2. Уровень 2: Целевой скрапинг по каждой найденной ссылке и фильтрация
    for item in target_results:
        # Используем URI из результатов Google для скрапинга
        product_data = scrape_product_details(item['uri'])
        if product_data:
            preliminary_results.append(product_data)
            
    if not preliminary_results:
        return {"error": f"После фильтрации по качеству данных (цена, изображение) не осталось результатов."}, 404

    # 3. Уровень 3: Сортировка по цене (приоритет фильтрации)
    # Сортируем от меньшей цены к большей
    final_results = sorted(preliminary_results, key=lambda x: x.get('price_value', float('inf')))

    return final_results, 200


# ==============================================================================
# FLASK ROUTE
# ==============================================================================

@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """
    Основная конечная точка для приема поисковых запросов.
    """
    if not request.json or 'query' not in request.json:
        return jsonify({"error": "Требуется JSON-тело с полем 'query'."}), 400

    query = request.json['query']
    
    # 1. Выполняем логику многоисточникового поиска
    results, status_code = execute_multi_source_search(query)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Добавляем маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return jsonify({
        "status": "ok", 
        "service": "psp-multi-search-backend (Aggregator)", 
        "search_engine": "Multi-Source Scraper",
        "priority": "Data Quality and Price"
    }), 200


# Запуск Gunicorn через BaseApplication
if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
