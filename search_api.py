from flask import Flask, request, jsonify

# Инициализация приложения Flask
app = Flask(__name__)

@app.route('/api/search', methods=['POST'])
def search_catalog():
    # --- БЛОК ОТЛАДКИ (ВРЕМЕННЫЙ КОД) ---
    
    # 1. Пытаемся получить входящие данные JSON
    try:
        data = request.get_json()
    except Exception as e:
        # Если JSON не пришел или невалиден
        return jsonify({
            "error": "Не удалось распарсить JSON-тело запроса.",
            "exception": str(e)
        }), 400

    # 2. Формируем ответ, включающий все полученные данные
    debug_response = {
        "status": "ОТЛАДКА УСПЕШНА (DEBUG SUCCESS)",
        "message": "Скрипт на сервере Render был успешно вызван и получил следующие данные:",
        "received_data": data,
        "received_query": data.get('query') if data and 'query' in data else 'Поле query не найдено',
        "method": request.method,
        "path": request.path
    }

    # 3. Возвращаем успешный ответ (200 OK) с отладочной информацией
    return jsonify(debug_response), 200

    # --- КОНЕЦ БЛОКА ОТЛАДКИ ---

# Это нужно, если вы запускаете локально, но Render использует Gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
