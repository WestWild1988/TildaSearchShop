# -*- coding: utf-8 -*-
# Этот файл является КОНЦЕПТУАЛЬНЫМ примером для развертывания на внешнем сервере (например, Render).
# Он имитирует работу API для поиска оборудования.

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import re

# Инициализация Flask приложения
app = Flask(__name__)
# Включаем CORS, чтобы запросы с вашего сайта Tilda не блокировались браузером.
CORS(app) 

# =============================================================================
# 1. СИМУЛЯЦИЯ БАЗЫ ДАННЫХ (Полный список товаров)
# =============================================================================

# Используем более разнообразный и структурированный набор данных для реалистичной фильтрации
ALL_PRODUCTS = [
    {"id": 1, "name": "Focusrite Scarlett 2i2 4th Gen", "price": 18000, "category": "Аудиоинтерфейсы", "brand": "Focusrite", "rank": 1},
    {"id": 2, "name": "Neumann TLM 103 Studio Set", "price": 120000, "category": "Микрофоны", "brand": "Neumann", "rank": 2},
    {"id": 3, "name": "Pioneer DJ XDJ-RX3 All-in-One", "price": 245000, "category": "DJ-Оборудование", "brand": "Pioneer DJ", "rank": 3},
    {"id": 4, "name": "Shure SM7B Vocal Microphone", "price": 38000, "category": "Микрофоны", "brand": "Shure", "rank": 4},
    {"id": 5, "name": "Yamaha HS8 Powered Studio Monitor", "price": 28000, "category": "Акустические системы", "brand": "Yamaha", "rank": 5},
    {"id": 6, "name": "Ableton Live 12 Standard License", "price": 40000, "category": "ПО", "brand": "Ableton", "rank": 6},
    {"id": 7, "name": "Novation Launchpad Pro MK3", "price": 32000, "category": "MIDI-Контроллеры", "brand": "Novation", "rank": 7},
    {"id": 8, "name": "Sennheiser HD 25 On-Ear DJ Headphones", "price": 14000, "category": "Наушники", "brand": "Sennheiser", "rank": 8},
    {"id": 9, "name": "M-Audio Oxygen Pro 49", "price": 19500, "category": "MIDI-Контроллеры", "brand": "M-Audio", "rank": 9},
    {"id": 10, "name": "KRK Rokit 5 G4 Monitor", "price": 15000, "category": "Акустические системы", "brand": "KRK", "rank": 10},
    {"id": 11, "name": "Rode NT1-A Complete Vocal Recording", "price": 25000, "category": "Микрофоны", "brand": "Rode", "rank": 11},
    {"id": 12, "name": "Behringer X32 Digital Mixer", "price": 450000, "category": "Микшеры", "brand": "Behringer", "rank": 12},
    {"id": 13, "name": "AKG K240 Studio Headphones", "price": 9000, "category": "Наушники", "brand": "AKG", "rank": 13},
    {"id": 14, "name": "Native Instruments Komplete 14 Ultimate", "price": 150000, "category": "ПО", "brand": "Native Instruments", "rank": 14},
    {"id": 15, "name": "Denon DJ SC6000 Prime", "price": 180000, "category": "DJ-Оборудование", "brand": "Denon DJ", "rank": 15},
    {"id": 16, "name": "Audio-Technica ATH-M50x", "price": 13500, "category": "Наушники", "brand": "Audio-Technica", "rank": 16},
    {"id": 17, "name": "Universal Audio Apollo Solo", "price": 42000, "category": "Аудиоинтерфейсы", "brand": "Universal Audio", "rank": 17},
    {"id": 18, "name": "Adam Audio T7V Monitor", "price": 20000, "category": "Акустические системы", "brand": "Adam Audio", "rank": 18},
    {"id": 19, "name": "Presonus Eris E5 XT", "price": 11000, "category": "Акустические системы", "brand": "Presonus", "rank": 19},
    {"id": 20, "name": "TC Helicon Voicelive 3", "price": 60000, "category": "Процессоры эффектов", "brand": "TC Helicon", "rank": 20},
]


# =============================================================================
# 2. ЛОГИКА ПОИСКА И ФИЛЬТРАЦИИ
# =============================================================================

def mock_search_results(query, category=None, brand=None, max_price=None):
    """
    Выполняет фильтрацию по полному списку товаров на основе
    запроса, категории, бренда и максимальной цены.
    """
    filtered_products = []
    
    # 1. Компилируем паттерн для поиска по запросу (регистронезависимый)
    query_pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None

    # 2. Фильтрация
    for product in ALL_PRODUCTS:
        
        # Фильтрация по поисковому запросу (query)
        if query_pattern:
            # Ищем совпадение в названии продукта
            if not query_pattern.search(product["name"]):
                continue # Пропускаем, если запрос не совпал
                
        # Фильтрация по категории (category)
        if category and category.lower() != 'все категории' and product["category"].lower() != category.lower():
            continue
            
        # Фильтрация по бренду (brand)
        if brand and brand.lower() != 'все бренды' and product["brand"].lower() != brand.lower():
            continue
            
        # Фильтрация по цене (max_price)
        # Если max_price указана, то цена продукта должна быть меньше или равна ей
        if max_price is not None and product["price"] > max_price:
            continue
            
        # Если все фильтры пройдены, добавляем товар
        filtered_products.append(product)
    
    # 3. Дополнительные поля для фронтенда и ограничение результата
    final_results = []
    
    # Сортируем по "rank" (моковая релевантность) для получения "лучших" результатов
    # Если rank отсутствует, используем id
    filtered_products.sort(key=lambda x: x.get('rank', x['id'])) 
    
    for i, product in enumerate(filtered_products[:15]): # Ограничение до 15 результатов
        # Добавляем специфические поля, которые ожидает ваш фронтенд
        name = product["name"]
        
        final_results.append({
            "id": product["id"],
            "title": name,
            "rank": product["rank"],
            "price": product["price"],
            "category": product["category"],
            "brand": product["brand"],
            # Создаем уникальную заглушку, использующую первую часть названия
            "image": f"https://placehold.co/128x128/0B4C6A/ffffff?text={name.split(' ')[0].split('-')[0]}", 
            "link": f"https://example.com/product/{product['id']}"
        })
        
    return final_results


# =============================================================================
# 3. API ENDPOINT
# =============================================================================

# Определяем API-эндпоинт для поиска
@app.route('/search', methods=['GET'])
def search_equipment():
    # Получаем параметры из запроса, отправленного из JavaScript (Tilda)
    query = request.args.get('query', '').strip()
    category = request.args.get('category', None)
    brand = request.args.get('brand', None)
    max_price_str = request.args.get('max_price', None)
    
    max_price = None
    if max_price_str:
        try:
            # Преобразуем цену в число
            # Цена приходит в копейках/центах, делим на 100 для корректного сравнения, если ваш JS отправляет ее так.
            # Если ваш JS отправляет цену как целое число (рубли/доллары), уберите деление на 100
            max_price = int(max_price_str)
        except ValueError:
            pass 

    # Выполняем поиск с новой, реалистичной логикой
    results = mock_search_results(query, category, brand, max_price)
    
    # Возвращаем результаты в формате JSON
    return jsonify({
        "status": "success",
        "results": results
    })

# Запуск приложения (только для локальной разработки)
if __name__ == '__main__':
    # Flask будет использовать стандартный порт 5000
    app.run(debug=True)
