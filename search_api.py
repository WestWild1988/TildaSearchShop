# -*- coding: utf-8 -*-
# Этот файл является КОНЦЕПТУАЛЬНЫМ примером для развертывания на внешнем сервере (например, Render).
# Он имитирует работу API для поиска оборудования.

from flask import Flask, request, jsonify
from flask_cors import CORS
import random

# Инициализация Flask приложения
app = Flask(__name__)
# Включаем CORS, чтобы запросы с вашего сайта Tilda не блокировались браузером.
# В production-среде лучше указать конкретный домен Tilda вместо "*"
CORS(app) 

# Моковые данные для имитации результатов поиска
# В реальном приложении здесь будет логика запроса к базе данных или парсинга
def mock_search_results(query, category=None, brand=None, max_price=None):
    """Генерирует 15 моковых результатов, имитируя данные с бэкенда."""
    results = []
    
    # Имитация списка популярных товаров
    product_names = [
        "Focusrite Scarlett 2i2 4th Gen",
        "Neumann TLM 103 Studio Set",
        "Pioneer DJ XDJ-RX3 All-in-One",
        "Shure SM7B Vocal Microphone",
        "Yamaha HS8 Powered Studio Monitor",
        "Ableton Live 12 Standard License",
        "Novation Launchpad Pro MK3",
        "Sennheiser HD 25 On-Ear DJ Headphones",
        "M-Audio Oxygen Pro 49 Keyboard",
        "Universal Audio Apollo Twin X Duo",
        "Rode NT1 Signature Series",
        "Akai Professional MPC One",
        "Korg Minilogue XD",
        "Native Instruments Komplete Kontrol S88",
        "Arturia MicroFreak Hybrid Synthesizer",
        "Midas M32R LIVE Digital Mixer",
        "Dynaudio LYD 5 Studio Monitors",
        "Electro-Voice EV ELX200-10P Speaker",
        "Boss Katana-50 MkII Guitar Amp",
        "Beyerdynamic DT 770 PRO 250 Ohm"
    ]

    for i in range(15):
        name = random.choice(product_names)
        price_rub = random.randint(10000, 990000)
        
        # Добавляем в описание имитацию совпадения с запросом
        description = f"Высококачественное оборудование. Отлично подходит для студии. Модель: {name.split(' ')[0]}-{random.randint(100, 999)}."
        if query and random.random() > 0.5:
             description = f"Специально для запроса '{query.upper()}': {description}"

        # Фильтр по цене (имитация)
        if max_price is not None and price_rub > max_price:
            continue
            
        results.append({
            "id": i + 1,
            "title": name,
            "description": description,
            "price": price_rub, # Цена в рублях
            "image": f"https://placehold.co/128x128/3b82f6/ffffff?text={name.split(' ')[0]}", # Изображение-заглушка
            "link": f"https://example.com/product/{i+1}"
        })
        
        # Убедимся, что возвращаем не более 15 результатов
        if len(results) >= 15:
            break
            
    return results

# Определяем API-эндпоинт для поиска
@app.route('/search', methods=['GET'])
def search_equipment():
    # Получаем параметры из запроса, отправленного из JavaScript (Tilda)
    query = request.args.get('query', '')
    category = request.args.get('category', None)
    brand = request.args.get('brand', None)
    max_price_str = request.args.get('max_price', None)
    
    max_price = None
    if max_price_str:
        try:
            # Преобразуем цену в число
            max_price = int(max_price_str)
        except ValueError:
            # Если цена невалидна, используем None
            pass 

    # Выполняем моковый поиск
    results = mock_search_results(query, category, brand, max_price)
    
    # Возвращаем результаты в формате JSON
    return jsonify({
        "status": "success",
        "query": query,
        "results": results
    })

# Точка входа для запуска (используется Gunicorn на Render)
# Gunicorn запускает приложение, используя 'gunicorn search_api:app'
if __name__ == '__main__':
    # Эта часть не используется на Render, но полезна для локального тестирования
    app.run(debug=True)
