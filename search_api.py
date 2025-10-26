from flask import Flask, request, jsonify
from flask_cors import CORS 
import random
import time
import re
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import requests 

# Инициализация приложения Flask
app = Flask(__name__)
# Включаем CORS для возможности запросов с фронтенда (index.html)
CORS(app) 

# --- КОНСТАНТЫ ДЛЯ РЕАЛЬНОГО (НО ОГРАНИЧЕННОГО) ПОИСКА ---
# Запросы направляются к Google Search с указанием локализации, 
# что имитирует поиск в РФ/СНГ. ВАЖНО: Это может быть нестабильно, 
# поэтому используется симуляция парсинга.
SEARCH_URL_RU = "https://www.google.com/search?hl=ru&gl=ru&q="
SEARCH_URL_EN = "https://www.google.com/search?hl=en&gl=us&q=" 
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- ФУНКЦИИ ОБРАБОТКИ ДАННЫХ (СИМУЛЯЦИЯ ИЗ-ЗА ОГРАНИЧЕНИЙ) ---

def extract_price(text: str) -> float:
    """
    ВНИМАНИЕ: Из-за нестабильности и блокировки со стороны внешних
    поисковых систем (Google, Яндекс) при автоматическом парсинге,
    данная функция генерирует случайную, но реалистичную цену.
    (Rule 2.2.c: Имитация цены).
    Генерирует случайную цену в диапазоне 15 000 - 65 000 рублей.
    """
    return random.randint(15000, 55000) + random.randint(0, 10000)

def extract_simulated_real_data(query: str, count: int = 20) -> list:
    """
    Симулирует извлечение реальных данных из нескольких источников
    на основе поискового запроса.
    """
    mock_sources = ["Яндекс.Маркет", "Ozon", "MusicStore.ru", "Avito Pro", "ProSound24.ru", "Baja.ru"]
    
    # Имитируем 20 результатов (Rule 2.4.a)
    simulated_results = []
    
    for i in range(1, count + 1):
        # Имитация изменения названия/модели в зависимости от "источника"
        model_name = query.replace('"', '').strip()
        
        # Генерируем название с вариациями
        title_template = random.choice([
            f"{model_name} Динамический Микрофон",
            f"Купить {model_name} в Москве",
            f"Комплект {model_name} с кабелем",
            f"Профессиональный микрофон {model_name}",
            f"{model_name} - {random.choice(['Лучшая цена', 'Акция', 'Скидка'])}",
        ])
        
        simulated_results.append({
            # Нам нужно только эти поля для фронтенда (Rule 2.3)
            "title": f"{title_template} (вариант {i})",
            "snippet": f"Описание товара и основные характеристики {model_name}. В наличии, быстрая доставка. Гарантия {random.choice([1, 2])} год(а).",
            "uri": f"https://example.com/product/{model_name.lower().replace(' ', '-')}/{i}",
            "source": random.choice(mock_sources),
            # price и rank будут добавлены позже
        })
        
    return simulated_results

def perform_google_search(query_ru: str, query_en: str) -> list:
    """
    Имитирует выполнение двуязычного поиска, обработку и ранжирование результатов.
    
    В реальном сценарии здесь должен был быть сложный парсинг и объединение данных.
    Здесь используется полностью симулированный процесс.
    """
    print(f"ЛОГ БЭКЕНДА: Запрос RU: '{query_ru}', Запрос EN: '{query_en}'")
    
    # 1. Имитация получения сырых данных (заглушка)
    # Используем только русский запрос для генерации данных.
    raw_results = extract_simulated_real_data(query_ru, count=20) 
    
    if not raw_results:
         print("ЛОГ БЭКЕНДА: Не удалось сгенерировать симулированные данные.")
         return []

    # 2. Постобработка и обогащение (Генерация цены и ранга)
    final_results = []
    for i, item in enumerate(raw_results):
        
        # Генерируем цену (Rule 2.3)
        price = extract_price(item['title']) 
        
        final_results.append({
            "id": i + 1,
            "title": item['title'],
            "snippet": item['snippet'],
            "uri": item['uri'],
            "source": item['source'],
            "price": price,
            "rank": 0, # Ранг будет установлен позже
        })

    # 3. Сортируем и устанавливаем ранг (Rule 2.4.b)
    # Фронтенд может пересортировать, но по правилам, бэкенд уже возвращает отсортированный список.
    final_results.sort(key=lambda x: x['price'])
    
    if final_results:
        # Устанавливаем ранг 1 для самого дешевого (Rule 2.3, 4.4)
        final_results[0]['rank'] = 1 
        final_results[0]['title'] += " ✨ (ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ!)" # Улучшаем титул для наглядности
        
        # Устанавливаем ранг 2 для второго по цене
        if len(final_results) > 1:
             final_results[1]['rank'] = 2 

    print(f"ЛОГ БЭКЕНДА: Сгенерировано и ранжировано {len(final_results)} результатов.")
    return final_results

# --- ГЛАВНЫЙ API ЭНДПОИНТ ---

@app.route('/api/search', methods=['POST'])
def search_aggregator():
    """
    Основной API-эндпоинт для выполнения поискового запроса.
    """
    start_time = time.time()
    
    # 1. Проверяем наличие JSON-тела
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Неверный формат JSON в теле запроса."}), 400

    # 2. Валидация входных данных (Rule 2.2.a)
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    # Используем первый запрос (русский) и второй (английский, если есть)
    query_ru = queries[0]
    # Фронтенд должен передавать перевод как второй элемент (Rule 2.2.b)
    query_en = queries[1] if len(queries) > 1 else query_ru 

    
    # 3. Вызываем функцию "реального" поиска
    try:
        # Запускаем поиск и обработку результатов
        results = perform_google_search(query_ru, query_en)
        
    except RequestException as e:
        # Обработка ошибок, связанных с внешними запросами 
        print(f"ЛОГ БЭКЕНДА: Критическая ошибка сети при выполнении поиска: {e}")
        return jsonify({"status": "error", "message": f"Критическая ошибка сети при подключении к поисковому сервису. Попробуйте снова. ({e})"}, 500)


    # 4. Возвращаем успешный ответ
    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    
    return jsonify({
        "status": "success",
        "query": query_ru, # Возвращаем русский запрос
        "execution_time_seconds": execution_time,
        "results_count": len(results),
        "results": results # Возвращаем отсортированные и ранжированные результаты
    })

# Точка входа для запуска (только для тестирования локально)
# В реальном продакшене эта часть часто не используется, 
# т.к. Flask запускается через WSGI-сервер (например, Gunicorn)
if __name__ == '__main__':
    # Включаем отладку для удобства разработки
    app.run(debug=True, port=5000)
