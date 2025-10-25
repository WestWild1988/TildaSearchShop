import os
import re
import json
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Tuple, Optional

# ==============================================================================
# КОНСТАНТЫ
# ==============================================================================

SCRAPE_TIMEOUT = 5
MAX_LINKS_TO_SCRAPE = 5 # Ограничиваем количество скрапируемых ссылок для демонстрации
REQUIRED_RESULTS_COUNT = 20 # Согласно Правилам, должно быть 20 уникальных карточек
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

app = Flask(__name__)
CORS(app)

# ==============================================================================
# ЭТАП 1: ПОЛУЧЕНИЕ ССЫЛОК (ИМИТАЦИЯ ВНЕШНЕГО ПОИСКА)
# ==============================================================================

def get_search_links(query: str) -> List[Dict]:
    """
    Имитирует вызов внешнего поисковика (Яндекс/Google) для получения 
    списка релевантных ссылок, имитируя как русскоязычные, так и англоязычные
    источники.

    В реальном приложении здесь будет логика вызова поискового API.
    Пока возвращаем захардкоженные ссылки для демонстрации.
    """
    # Имитация различных источников для разнообразия доменов и цен
    source_templates = {
        # Высокая цена, известные бренды
        "Shure SM58": [
            {"uri": "https://music-shop-pro.ru/shure-sm58", "source_domain": "music-shop-pro.ru", "price_base": 15500, "base_rank": 3},
            {"uri": "https://sound-store.com/shure-sm58-mic", "source_domain": "sound-store.com", "price_base": 16000, "base_rank": 4},
        ],
        # Средняя цена, популярные модели
        "JBL speakers": [
            {"uri": "https://pult.ru/jbl-monitor", "source_domain": "pult.ru", "price_base": 9000, "base_rank": 2},
            {"uri": "https://rusound.ru/jbl-305p", "source_domain": "rusound.ru", "price_base": 8800, "base_rank": 1},
        ],
        # Низкая цена, аксессуары или б/у
        "Гитарный кабель": [
            {"uri": "https://avito.ru/cable-vga", "source_domain": "avito.ru", "price_base": 1200, "base_rank": 1},
            {"uri": "https://aliexpress.com/pro-cable", "source_domain": "aliexpress.com", "price_base": 900, "base_rank": 2},
        ],
        # Нечто среднее
        "Конденсаторный микрофон": [
            {"uri": "https://ozon.ru/mic-usb", "source_domain": "ozon.ru", "price_base": 4500, "base_rank": 3},
            {"uri": "https://wildberries.ru/mic-bm800", "source_domain": "wildberries.ru", "price_base": 4200, "base_rank": 2},
        ]
    }

    # Поиск соответствующего шаблона
    query_key = next((key for key in source_templates if key.lower() in query.lower()), None)
    
    if query_key:
        links = source_templates[query_key]
    else:
        # Для любого другого запроса генерируем случайный набор ссылок
        links = [
            {"uri": f"https://random-store-{i}.com/{query.lower().replace(' ', '-')}", 
             "source_domain": f"random-store-{i}.com", 
             "price_base": random.randint(3000, 25000), 
             "base_rank": random.randint(1, 4)}
            for i in range(MAX_LINKS_TO_SCRAPE)
        ]

    # Добавляем 15 дополнительных "шумовых" результатов для наполнения до 20
    noise_links = [
        {"uri": f"https://vendor-{i}.com/product-{random.randint(1000, 9999)}", 
         "source_domain": f"vendor-{i}.com", 
         "price_base": random.randint(1000, 50000), 
         "base_rank": 5}
        for i in range(REQUIRED_RESULTS_COUNT - len(links))
    ]
    
    # Объединяем ссылки и берем MAX_LINKS_TO_SCRAPE + REQUIRED_RESULTS_COUNT-N
    all_links = (links + noise_links)[:REQUIRED_RESULTS_COUNT]
    
    # Добавляем случайное смещение к цене для имитации разных предложений
    for link in all_links:
        link['price_value'] = link['price_base'] + random.randint(-500, 500)
        link['price_value'] = max(100, link['price_value']) # Цена не может быть < 100
    
    return all_links

# ==============================================================================
# ЭТАП 2: СКРАПИНГ ОТДЕЛЬНОЙ СТРАНИЦЫ (ИМИТАЦИЯ)
# ==============================================================================

def scrape_product_page(link_data: Dict) -> Optional[Dict]:
    """
    Имитирует скрапинг конкретной страницы товара для извлечения 
    финальных данных, используя захардкоженные значения.
    """
    # Имитация получения данных с помощью BeautifulSoup
    
    # Генерация случайных/фиктивных данных для заполнения полей
    domain = link_data.get('source_domain', 'unknown.com')
    base_price = link_data['price_value']
    
    # Фиктивные заголовки и описания
    if 'shure' in domain:
        title = "Микрофон Shure SM58 - Легенда Вокала"
        snippet = "Динамический кардиоидный микрофон для живых выступлений. Прочный, надежный, стандарт индустрии."
        img_url = "https://placehold.co/300x200/2563eb/FFFFFF?text=Shure+SM58"
    elif 'jbl' in domain or 'rusound' in domain:
        title = "JBL 305P MkII - Активный студийный монитор"
        snippet = "Студийный монитор ближнего поля с технологией Image Control Waveguide, 5-дюймовым вуфером."
        img_url = "https://placehold.co/300x200/f59e0b/FFFFFF?text=JBL+Monitor"
    else:
        title = f"Профессиональное Оборудование: {domain} #ID{random.randint(1000, 9999)}"
        snippet = f"Универсальный товар с ${domain} для сцены или студии. Лучшая цена в своем классе."
        img_url = f"https://placehold.co/300x200/{random.choice(['059639', 'ef4444', '10b981'])}/FFFFFF?text=PSP+Gear"

    # Формирование финального объекта
    return {
        "title": title,
        "snippet": snippet,
        "uri": link_data['uri'],
        "source_domain": domain,
        "price_raw": f"{base_price:,.0f} ₽".replace(',', ' '), # Форматированный текст цены
        "price_value": base_price, # Числовое значение для сортировки
        "image_url": img_url,
        "rank": link_data['base_rank'] # Временный ранг, будет пересчитан позже
    }


# ==============================================================================
# ОСНОВНАЯ ЛОГИКА ПОИСКА И РАНЖИРОВАНИЯ
# ==============================================================================

def two_stage_search(queries: List[str]) -> Tuple[List[Dict], int]:
    """
    Выполняет двухэтапный поиск для всех запросов в списке queries:
    1. Получает список ссылок (имитация поиска).
    2. Скрапит каждую ссылку (имитация извлечения данных).
    3. Объединяет результаты, удаляет дубликаты и ранжирует.
    
    :param queries: Массив поисковых запросов.
    :return: Кортеж (список результатов, HTTP-статус-код).
    """
    if not queries or not isinstance(queries, list):
        return {"error": "Массив 'queries' не предоставлен или не является списком."}, 400

    all_raw_results = {} # Словарь для хранения результатов по URI (для дедупликации)

    # 1. Сбор ссылок по всем запросам
    for query in queries:
        search_links = get_search_links(query)
        
        # 2. Имитация скрапинга и сборка
        for link_data in search_links:
            # Используем URI как ключ для дедупликации
            uri = link_data['uri']
            
            # Имитация таймаута при скрапинге (случайно)
            if random.random() < 0.1: # 10% шанс имитировать таймаут
                print(f"Имитация таймаута для URI: {uri}. Пропуск.")
                continue

            product_data = scrape_product_page(link_data)
            
            if product_data:
                # Если URI уже есть, обновляем, если новая цена ниже
                if uri in all_raw_results:
                    if product_data['price_value'] < all_raw_results[uri]['price_value']:
                        all_raw_results[uri] = product_data
                else:
                    all_raw_results[uri] = product_data
            
    final_results = list(all_raw_results.values())

    # 3. Фильтрация и ранжирование
    
    if not final_results:
        # Для удобства тестирования, если ничего не найдено, возвращаем пустой список
        return [], 200

    # Сортировка по цене (по возрастанию)
    final_results.sort(key=lambda x: x.get('price_value', float('inf')))

    # Присвоение финального ранга
    min_price = final_results[0]['price_value'] if final_results else None
    
    for idx, item in enumerate(final_results):
        # Ранг 1 присваивается только товарам с минимальной ценой
        item['rank'] = 1 if item['price_value'] == min_price else idx + 1

    # Убеждаемся, что возвращаем ровно REQUIRED_RESULTS_COUNT уникальных элементов
    # (Хотя логика выше должна возвращать 20, т.к. мы наполнили список шумовыми данными)
    return final_results[:REQUIRED_RESULTS_COUNT], 200


# ==============================================================================
# FLASK ROUTE
# ==============================================================================

@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """
    Основная конечная точка для приема поисковых запросов.
    Ожидает JSON-тело с полем 'queries': list[str].
    """
    if not request.json or 'queries' not in request.json or not isinstance(request.json['queries'], list):
        return jsonify({"error": "Требуется JSON-тело с полем 'queries' (массив строк)."}, 
                       "Правила требуют массив запросов, а не одиночную строку 'query'."), 400

    queries = request.json['queries']
    
    # 1. Выполняем логику двухэтапного поиска
    results, status_code = two_stage_search(queries)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Добавляем маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return jsonify({"status": "ok", "service": "psp-search-backend (Two-Stage Scraping Demo)", 
                    "notes": "API ожидает массив 'queries' (list[str]) в POST-запросе к /api/search"}), 200

# Добавляем маршрут для проверки тестового поиска
@app.route('/api/test', methods=['GET'])
def test_search():
    """
    Тестовая конечная точка для проверки логики без фронтенда.
    """
    test_queries = ["Shure SM58", "JBL колонки (Eng. Equivalent)"]
    results, status_code = two_stage_search(test_queries)
    return jsonify(results), status_code

if __name__ == '__main__':
    # Эта часть будет игнорироваться в среде Canvas, но полезна для локального тестирования
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
