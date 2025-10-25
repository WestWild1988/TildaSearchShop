import os
import json
from flask import Flask, request, jsonify
from google import genai
from google.genai.errors import APIError
from gunicorn.app.base import BaseApplication

app = Flask(__name__)

# ==============================================================================
# КОНФИГУРАЦИЯ GEMINI & API
# ==============================================================================

# Проверяем переменную окружения. Render автоматически загрузит ключ,
# который вы должны установить в настройках сервиса Render.
try:
    API_KEY = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=API_KEY)
    client = genai.Client()
    print("INFO: Gemini Client инициализирован.")
except KeyError:
    print("FATAL: Переменная окружения 'GEMINI_API_KEY' не найдена.")
    client = None
except Exception as e:
    print(f"FATAL: Ошибка инициализации Gemini Client: {e}")
    client = None

# ==============================================================================
# ФУНКЦИИ БЭКЕНД-ЛОГИКИ
# ==============================================================================

def execute_google_search(query: str):
    """
    Выполняет поиск через Gemini API с использованием инструмента Google Search.
    
    Args:
        query: Пользовательский поисковый запрос.
        
    Returns:
        Список источников в формате, ожидаемом фронтендом, или сообщение об ошибке.
    """
    if not client:
        return {"error": "API Key не установлен или клиент не инициализирован."}, 500

    # Запрос к модели: просим сгенерировать короткий сниппет и используем Google Search
    prompt = f"Найди в Интернете информацию по запросу и дай краткий ответ. Основной запрос: {query}"
    
    print(f"INFO: Отправка запроса в Gemini: '{prompt}'")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-09-2025',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                tools=[{"google_search": {}}] # Включаем Google Search Grounding
            ),
        )

        # 1. Извлекаем метаданные заземления (Grounding Attributions)
        grounding_metadata = response.candidates[0].grounding_metadata if response.candidates and response.candidates[0].grounding_metadata else None
        
        if not grounding_metadata or not grounding_metadata.grounding_attributions:
            # Если нет аттрибуций (ссылок), возвращаем ошибку, так как фронтенд ждет источники
            return {"error": "Поиск не дал источников (Grounding Attributions пуст)."}, 404

        # 2. Форматируем источники в нужный формат: {title, snippet, uri}
        results = []
        for attr in grounding_metadata.grounding_attributions:
            if attr.web:
                # В качестве snippet используем текст, который модель связала с этим источником,
                # или сам текст, сгенерированный моделью, если это возможно.
                # В данной реализации используем title и uri из Google Search
                results.append({
                    "title": attr.web.title if attr.web.title else "Источник без названия",
                    "uri": attr.web.uri,
                    # Используем snippet из самого аттрибута, если доступен.
                    "snippet": attr.web.snippet if attr.web.snippet else "Краткое описание недоступно. Перейдите по ссылке для получения деталей."
                })
        
        print(f"INFO: Успешно извлечено {len(results)} источников.")
        return results, 200

    except APIError as e:
        print(f"ERROR: Ошибка Gemini API: {e}")
        return {"error": f"Ошибка Gemini API: {e}"}, 500
    except Exception as e:
        print(f"ERROR: Неожиданная ошибка: {e}")
        return {"error": f"Внутренняя ошибка сервера: {e}"}, 500


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
    
    # 1. Выполняем основную логику поиска
    results, status_code = execute_google_search(query)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Добавляем маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return jsonify({"status": "ok", "service": "psp-search-backend", "client_initialized": client is not None}), 200


# Запуск Gunicorn через BaseApplication для упрощения запуска в Render
# В production используется Gunicorn, но это нужно для локального тестирования
if __name__ == '__main__':
    # Эта часть не используется Render, но полезна для локального тестирования.
    print("WARN: Запуск локального тестового сервера (используйте gunicorn в prod).")
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
