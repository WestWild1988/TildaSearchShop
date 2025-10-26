from flask import Flask, request, jsonify
import random # Используем для генерации случайных цен

# Инициализация приложения Flask
app = Flask(__name__)

# --- ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ MOCK-ДАННЫХ (для соответствия требованиям фронтенда) ---
def generate_mock_results(query):
    """Генерирует 20 структурированных результатов для имитации реального поиска."""
    mockData = []
    # Базовая цена для разнообразия
    basePrice = random.randint(10000, 60000) 

    for i in range(20):
        # Генерируем цену, слегка отличающуюся от базовой
        price = basePrice + (1000 * i) - (500 * (i % 2))
        # Присваиваем rank 1 только первому элементу, остальные случайные
        rank = 1 if i == 0 else random.randint(2, 6)
        
        mockData.append({
            "id": i + 1,
            "title": f"{query} — Результат №{i + 1}",
            "snippet": f"Краткое описание товара, найденного по запросу '{query}' в интернет-источнике.",
            "uri": f"https://example.com/item/{i + 1}",
            "source": f"Источник {chr(65 + i // 5)}", # A, B, C, D
            "price": max(100, price), # Цена не может быть меньше 100
            "rank": rank 
        })
    
    # Сортируем по цене, как требует фронтенд, чтобы имитировать реальную логику
    mockData.sort(key=lambda x: x['price'])
    return mockData

@app.route('/api/search', methods=['POST'])
def search_catalog():
    # 1. Обработка входящего JSON
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Не удалось распарсить JSON-тело запроса."}), 400

    # 2. Извлекаем массив 'queries', который отправляет фронтенд
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    # Используем первый запрос из массива для генерации Mock-данных
    query_to_use = queries[0]
    results = generate_mock_results(query_to_use)

    # 3. Возвращаем успешный ответ со структурой, которую ожидает фронтенд
    # (массив results с полями title, snippet, uri, source, price, rank)
    return jsonify({
        "status": "success",
        "query_used": query_to_use,
        "results_count": len(results),
        "results": results # Главный массив данных
    }), 200

# Это нужно, если вы запускаете локально, но Render использует Gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
