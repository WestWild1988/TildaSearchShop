import os
import re
import time
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
# Библиотеки requests, BeautifulSoup и urlparse импортированы,
# но используются только в имитационных функциях.
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
    Генерирует REQUIRED_RESULTS (20) уникальных, реалистичных 
    мок-результатов для пагинации.
    
    Результат должен содержать поля: title, snippet, uri, source, price, rank.
    """
    results = []
    
    # База для генерации данных
    base_title = query.title()
    sources = ["MusicMagazin.ru", "ProAudioShop.ru", "DJ-Equipment.com", "StudioGear.net", "A&T Trade"]
    domains = ["musicmagazin.ru", "proaudiotrade.com", "djequip.biz", "studiogear.tech", "attrade.ru"]
    
    # Генерируем уникальные цены и ранги.
    prices = sorted([random.randint(15000, 45000) for _ in range(REQUIRED_RESULTS)])
    
    for i in range(REQUIRED_RESULTS):
        source_name = random.choice(sources)
        source_domain = domains[sources.index(source_name)]
        
        # Эмуляция разных модификаций товара
        suffix = random.choice([" (Черный)", " (Серый)", " Pro", " Lite", " II", ""])
        
        # Генерация мок-результата
        result = {
            "title": f"{base_title}{suffix} - Купить в {source_name}",
            "snippet": f"Профессиональное аудиооборудование для студии. Модель {base_title} с гарантией и доставкой по РФ и СНГ.",
            "uri": f"https://www.{source_domain}/products/{query.lower().replace(' ', '-')}-{i+1}",
            "source": source_name,
            "price": prices[i], # Сортируем по цене на фронтенде
            "rank": i + 1, # Временный ранг, который может быть использован для индикации "Лучшее предложение"
        }
        results.append(result)

    # Принудительно ставим самый низкий ранг (1) для самого дешевого товара
    # (который будет первым после сортировки на фронте), имитируя лучшее предложение.
    # Так как мы генерируем цены отсортированными, самый первый элемент
    # в списке results будет самым дешевым.
    if results:
        results[0]['rank'] = 1 
        results[0]['title'] = f"💥 ЛУЧШАЯ ЦЕНА! {results[0]['title']}"

    print(f"[{time.strftime('%H:%M:%S')}] Сгенерировано {len(results)} мок-результатов для запроса '{query}'.")
    
    return results

# ==============================================================================
# ЭТАП 1: ПОЛУЧЕНИЕ ССЫЛОК (ИМИТАЦИЯ ВНЕШНЕГО ПОИСКА)
# ==============================================================================

def get_search_links(base_query: str, count: int) -> list[str]:
    """
    Имитирует вызов реального поисковика (например, Yandex или Google) 
    и получение списка URL для дальнейшего скрапинга.
    """
    # Имитация задержки внешнего API
    time.sleep(random.uniform(0.5, 1.5)) 
    
    # Генерируем mock-URL, которые будут "скрапиться" на следующем этапе.
    # Мы знаем, что следующий этап использует generate_mock_results, 
    # поэтому реальный скрапинг здесь не требуется.
    mock_links = [f"http://mock-link-for-scrape.com/item/{i}" for i in range(count)]
    print(f"[{time.strftime('%H:%M:%S')}] Этап 1: Получено {len(mock_links)} мок-ссылок.")
    
    return mock_links

# ==============================================================================
# ЭТАП 2: ДЕТАЛЬНЫЙ СКРАПИНГ (ИМИТАЦИЯ)
# ==============================================================================

def scrape_single_link(url: str, query: str) -> dict | None:
    """
    Имитирует глубокий скрапинг одной страницы для извлечения 
    конкретной информации о товаре.
    
    В реальной ситуации здесь был бы requests.get(url) и BS4 парсинг.
    """
    print(f"[{time.strftime('%H:%M:%S')}] Имитация скрапинга: {url}")
    
    # Имитация задержки скрапинга (имитация сетевого ожидания)
    time.sleep(random.uniform(0.1, 0.5)) 

    # Поскольку мы не можем реально скрапить URL, мы просто возвращаем 
    # сгенерированный мок-результат, используя функцию с генератором.
    # Для демонстрации мы берем один результат из 20 сгенерированных.
    mock_data = generate_mock_results(query)
    
    # Чтобы имитировать, что некоторые скрапинги могут потерпеть неудачу,
    if random.random() < 0.1: # 10% шанс неудачи
        print(f"[{time.strftime('%H:%M:%S')}] ОШИБКА: Скрапинг {url} имитировал сбой.")
        return None
    
    # Возвращаем один случайный результат из сгенерированных мок-данных
    return random.choice(mock_data) if mock_data else None


# ==============================================================================
# ОСНОВНАЯ ЛОГИКА АПИ: ДВУХЭТАПНЫЙ ПОИСК
# ==============================================================================

def two_stage_search(query: str) -> tuple[list[dict], int]:
    """
    Выполняет двухэтапный процесс:
    1. Получает список релевантных ссылок (имитация).
    2. Скрапит каждую ссылку, пока не получит REQUIRED_RESULTS (имитация).
    """
    print(f"[{time.strftime('%H:%M:%S')}] Начат двухэтапный поиск по запросу: {query}")
    
    # 1. Этап 1: Получение ссылок
    # Для целей демонстрации мы не будем вызывать get_search_links, 
    # а сразу сгенерируем все необходимые 20 результатов
    # и вернем их как финальный результат, имитируя, что все ссылки
    # успешно обработаны на Этапе 2.
    
    try:
        # Имитация получения 20 финальных результатов после скрапинга
        # (включая сортировку и ранжирование)
        final_results = generate_mock_results(query)
        
        if len(final_results) >= REQUIRED_RESULTS:
            print(f"[{time.strftime('%H:%M:%S')}] УСПЕХ: Найдено {len(final_results)} результатов (цель {REQUIRED_RESULTS}).")
            return final_results, 200
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ПРЕДУПРЕЖДЕНИЕ: Найдено только {len(final_results)} результатов.")
            return final_results, 200 # Возвращаем то, что есть, со статусом 200
            
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] КРИТИЧЕСКАЯ ОШИБКА в two_stage_search: {e}")
        return jsonify({"error": f"Внутренняя ошибка API при обработке запроса: {e}"}), 500
        
    # Этот код никогда не должен быть достигнут, но оставлен для надежности
    return jsonify({"error": f"Результатов не найдено после двухэтапного поиска по запросу: {query}"}), 404
            
    # return final_results, 200 # Для простоты демонстрации всегда возвращаем 200

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
    return jsonify({
        "status": "ok", 
        "service": "psp-search-backend (Mock Two-Stage Search)",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

# ==============================================================================
# ЗАПУСК СЕРВЕРА FLASK
# ==============================================================================

if __name__ == '__main__':
    # Очищаем логику двухэтапного поиска перед запуском (просто печать)
    print("==================================================================")
    print(f"  PSP Mock Search API запущен (Flask)  ")
    print(f"  Целевое количество результатов: {REQUIRED_RESULTS}")
    print("  Для проверки: POST-запрос на /api/search с телом: ")
    print("  {'queries': ['Shure SM58', 'Шур СМ58']")
    print("==================================================================")
    # Используем 0.0.0.0 и порт 5000 для совместимости с docker/хостингом
    app.run(debug=True, host='0.0.0.0', port=5000)
