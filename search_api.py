import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup

# Импортируем библиотеки для скрапинга
import requests

app = Flask(__name__)
# Включаем CORS, чтобы фронтенд мог обращаться к этому API
CORS(app)

# ==============================================================================
# МОДЕЛЬНЫЙ HTML-КОНТЕНТ ДЛЯ СКРАПИНГА
# Имитация страницы каталога для демонстрации работы с BeautifulSoup
# ==============================================================================

# Этот HTML-код основан на фрагменте, который вы загружали ранее (PageSound)
MOCK_HTML_CONTENT = """
<div class="cont-product_sect clearfix">
    <a href="/catalog/dj_oborudovanie/" class="cat-body_item">
        <div class="title"><span>DJ-оборудование</span></div>
    </a>
    <a href="/catalog/akusticheskie_sistemy/" class="cat-body_item">
        <div class="title"><span>Акустические системы</span></div>
    </a>
    <a href="/catalog/mikrofony/" class="cat-body_item">
        <div class="title"><span>Микрофоны студийные и вокальные</span></div>
    </a>
    <a href="/catalog/usiliteli/" class="cat-body_item">
        <div class="title"><span>Усилители мощности</span></div>
    </a>
    <a href="/catalog/mikrofony_shure/" class="cat-body_item">
        <div class="title"><span>Микрофоны Shure (Официальный дилер)</span></div>
    </a>
    <a href="/catalog/behringer/" class="cat-body_item">
        <div class="title"><span>Оборудование Behringer</span></div>
    </a>
</div>
"""

# ==============================================================================
# ФУНКЦИИ БЭКЕНД-ЛОГИКИ (Скрапинг)
# ==============================================================================

def execute_catalog_search(query: str):
    """
    Выполняет поиск в модельном HTML-каталоге, используя BeautifulSoup.
    
    Args:
        query: Пользовательский поисковый запрос.
        
    Returns:
        Список источников в формате, ожидаемом фронтендом.
    """
    # Преобразуем запрос в нижний регистр для нечувствительного к регистру поиска
    search_query = query.lower()
    
    # 1. Парсим модельный HTML-контент
    soup = BeautifulSoup(MOCK_HTML_CONTENT, 'html.parser')
    
    # Ищем все ссылки на категории товаров
    category_links = soup.find_all('a', class_='cat-body_item')
    
    results = []
    
    for link in category_links:
        title_span = link.find('span')
        title = title_span.text.strip() if title_span else "Категория без названия"
        uri = link.get('href', '#')
        
        # 2. Проверяем, соответствует ли название категории поисковому запросу
        if search_query in title.lower():
            # Форматируем результат, как того ожидает фронтенд
            results.append({
                "title": title,
                "uri": "https://example.com" + uri, # Добавляем базовый домен
                "snippet": f"Каталог товаров по категории '{title}'. Найдено по запросу '{query}'."
            })

    print(f"INFO: Успешно найдено {len(results)} результатов для запроса '{query}'.")
    
    if not results:
        # Если ничего не найдено, возвращаем 404
        return {"error": f"Ничего не найдено в каталоге по запросу: {query}"}, 404
        
    return results, 200


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
    
    # 1. Выполняем логику поиска/скрапинга
    results, status_code = execute_catalog_search(query)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Добавляем маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return jsonify({"status": "ok", "service": "psp-search-backend (Scraping version)", "search_engine": "BeautifulSoup"}), 200


# Запуск Gunicorn через BaseApplication для упрощения запуска в Render
# В production используется Gunicorn, но это нужно для локального тестирования
if __name__ == '__main__':
    # Эта часть не используется Render, но полезна для локального тестирования.
    print("WARN: Запуск локального тестового сервера (используйте gunicorn в prod).")
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
