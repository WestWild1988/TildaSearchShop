from flask import Flask, request, jsonify
import random
import time

# Инициализация приложения Flask
app = Flask(__name__)

# --- ФУНКЦИЯ ДЛЯ ИМИТАЦИИ ПАРСИНГА И ПОИСКА ---
def perform_mock_search(query):
    """
    Имитирует выполнение поиска и возвращает структурированный Mock-массив 
    с 20 результатами, включая все необходимые поля:
    title, snippet, uri, source, price, rank.
    """
    print(f"Выполнение имитации запроса к внешнему источнику для: {query}")
    # Имитация сетевой задержки, чтобы приблизить к реальным условиям
    time.sleep(0.5) 
    
    # --- СЕКЦИЯ МОК-ДАННЫХ, КОТОРУЮ НЕОБХОДИМО ЗАМЕНИТЬ РЕАЛЬНОЙ ЛОГИКОЙ ПАРСИНГА ---
    
    mockData = []
    # Базовая цена для вариаций
    basePrice = random.randint(10000, 60000) 

    for i in range(20):
        # Генерируем данные с учетом реальных полей, ожидаемых фронтендом
        price = basePrice + (1000 * i) - (500 * (i % 2))
        # Ранг 1 для первого элемента, остальные случайны
        rank = 1 if i == 0 else random.randint(2, 6)
        
        mockData.append({
            "id": i + 1,
            "title": f"Моковый результат {i + 1}: {query}",
            "snippet": f"Описание продукта {i + 1}. Это высококачественное PSP оборудование.",
            "uri": f"https://mock-source-{random.randint(1, 4)}.ru/item/{i + 1}",
            "source": f"Магазин-{random.randint(1, 4)}",
            "price": price, # Цена в рублях (₽)
            "rank": rank
        })
        
    # Возвращаем имитированные данные
    return mockData


# API маршрут, который принимает как GET (для проверки), так и POST (для реальной работы)
@app.route('/api/search', methods=['GET', 'POST'])
def search_catalog():
    if request.method == 'GET':
        # Если это GET-запрос (из браузера), возвращаем инструкцию
        return jsonify({
            "status": "info",
            "message": "API маршрут активен. Используйте метод POST с JSON-телом {'queries': ['ваш запрос']} для поиска."
        }), 200

    # Если это POST-запрос, выполняем основную логику
    
    # 1. Обработка входящего JSON
    try:
        data = request.get_json()
    except Exception:
        # 400 Bad Request
        return jsonify({"error": "Не удалось распарсить JSON-тело запроса."}), 400

    # 2. Извлекаем массив 'queries', который отправляет фронтенд
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        # 400 Bad Request
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    # Используем первый запрос из массива для выполнения поиска
    query_to_use = queries[0]
    
    # Вызываем функцию, имитирующую поиск
    results = perform_mock_search(query_to_use)

    # 3. Возвращаем успешный ответ
    return jsonify({
        "status": "success",
        "query": query_to_use,
        "results": results
    }), 200

if __name__ == '__main__':
    # В реальной среде это не выполняется, но полезно для локального тестирования
    print("Запуск Flask-сервера...")
    app.run(debug=True, port=5000)
