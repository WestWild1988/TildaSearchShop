from flask import Flask, request, jsonify
from flask_cors import CORS 
import time
import re
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import requests 

# Инициализация приложения Flask
app = Flask(__name__)
CORS(app) 

# --- КОНСТАНТЫ ДЛЯ РЕАЛЬНОГО ПОИСКА ---
# Запросы направляются к Google Search с указанием локализации RU
SEARCH_URL_RU = "https://www.google.com/search?hl=ru&gl=ru&q="
# Для двуязычности (хотя парсим только RU, EN запрос используется для архитектуры)
SEARCH_URL_EN = "https://www.google.com/search?hl=en&gl=us&q=" 
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- ФУНКЦИИ РЕАЛЬНОГО ПАРСИНГА ---

def extract_price_and_source(text: str) -> tuple[float, str]:
    """
    Пытается извлечь реальную цену и источник из сниппета или заголовка.
    Возвращает (price: float, source: str).
    Если цена не найдена, возвращает 999999.0 и "Неизвестный Источник".
    """
    
    # 1. Извлечение цены (поиск чисел, похожих на рубли или общую цену)
    
    # Регулярное выражение для поиска цен: число с пробелами или запятыми, 
    # за которым может следовать 'руб', 'р', '₽' или 'USD', 'EUR'.
    # Мы отдаем предпочтение большим числам (цены на оборудование)
    price_match = re.search(r'(\d[\s\d\.\,]*)\s*(?:руб|р\.|₽|USD|EUR)', text, re.IGNORECASE)
    
    if price_match:
        price_str = price_match.group(1).replace(' ', '').replace(',', '.')
        try:
            # Преобразуем в число. Если это USD/EUR, делаем грубую конвертацию для симуляции РФ рынка.
            price = float(price_str)
            if 'USD' in price_match.group(0).upper() or 'EUR' in price_match.group(0).upper():
                price = price * 80 # Грубый курс для имитации рублевой цены
            
            # Убеждаемся, что цена выглядит как цена оборудования, а не как дата
            if price < 1000:
                 return 999999.0, "Неизвестный Источник"

            return round(price, 2), "Парсинг Цены"
        except ValueError:
            pass
    
    # 2. Поиск крупных торговых площадок как источника
    source = "Неизвестный Источник"
    for s in ["Яндекс.Маркет", "Ozon", "AliExpress", "Avito", "MusicStore.ru"]:
        if s.lower() in text.lower():
            source = s
            break
            
    # Если цена не найдена, используем очень высокую цену для отправки в конец списка
    return 999999.0, source


def extract_real_data(soup: BeautifulSoup) -> list:
    """
    Парсит HTML-суп Google для извлечения 20 структурированных результатов.
    Пытается извлечь title, snippet, uri и вызывает функцию для price/source.
    """
    results = []
    
    # Поиск всех основных блоков результатов
    # Ищем все контейнеры, содержащие ссылки
    search_results = soup.find_all('div', class_='g')
    
    for div_result in search_results:
        # Ищем заголовок (h3) и ссылку (a) внутри блока
        h3_title = div_result.find('h3')
        a_tag = div_result.find('a')
        snippet_div = div_result.find('div', class_='VwiC3b') or div_result.find('span', class_='aCOpRe')
        
        if h3_title and a_tag and 'href' in a_tag.attrs:
            title = h3_title.get_text()
            uri = a_tag['href']
            snippet = snippet_div.get_text() if snippet_div else "Сниппет не найден."
            
            # 1. Очищаем URI
            match = re.search(r'/url\?q=([^&]+)', uri)
            if match:
                uri = match.group(1)
            
            # 2. Реальное извлечение цены и источника
            price, source = extract_price_and_source(title + " " + snippet)

            results.append({
                "id": len(results) + 1,
                "title": title,
                "snippet": snippet,
                "uri": uri,
                "source": source,
                "price": price,
                "rank": 0,
            })
        
        if len(results) >= 20: # Rule 2.4.a: ограничение до 20
            break

    # 3. Сортируем и устанавливаем ранг (Rule 2.4.b)
    # Сортируем по цене (самая низкая - первая)
    results.sort(key=lambda x: x['price'])
    
    if results:
        # Устанавливаем ранг 1 для самого дешевого
        results[0]['rank'] = 1 
        results[0]['title'] += " [ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ!]"

    print(f"ЛОГ БЭКЕНДА: Возвращается {len(results)} отсортированных результатов после реального парсинга.")
    return results


def perform_google_search(query_ru: str, query_en: str) -> list:
    """
    Выполняет реальный HTTP-запрос к Google Search и парсит результаты.
    Используется русский запрос (query_ru) для поиска в РФ/СНГ локализации.
    """
    # Используем русский запрос и локализацию
    url = SEARCH_URL_RU + requests.utils.quote(query_ru)
    
    headers = {'User-Agent': USER_AGENT}
    
    print(f"ЛОГ БЭКЕНДА: Выполняется РЕАЛЬНЫЙ HTTP-запрос к Google (RU): {url}")
    
    # Имитация задержки сети и обхода блокировок
    time.sleep(2) 
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status() # Вызовет исключение при плохих статусах (4xx, 5xx)

    # Парсинг и обработка
    soup = BeautifulSoup(response.text, 'html.parser')
    results = extract_real_data(soup)
    
    return results

# --- API МАРШРУТ ---

@app.route('/api/search', methods=['GET', 'POST'])
def search_catalog():
    start_time = time.time()
    
    if request.method == 'GET':
        return jsonify({
            "status": "info",
            "message": "API маршрут активен. Используйте метод POST с JSON-телом {'queries': ['ваш запрос']} для реального поиска."
        }), 200

    # Обработка POST-запроса
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"status": "error", "message": "Не удалось распарсить JSON-тело запроса."}), 400

    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    query_ru = queries[0]
    query_en = queries[1] if len(queries) > 1 else query_ru 

    # Вызываем функцию реального поиска
    try:
        results = perform_google_search(query_ru, query_en)
        
    except RequestException as e:
        # Обработка ошибок, связанных с внешними запросами 
        print(f"ЛОГ БЭКЕНДА: Критическая ошибка сети/CAPTHA при выполнении поиска: {e}")
        # Возвращаем понятное сообщение об ошибке
        return jsonify({
            "status": "error", 
            "message": f"Ошибка поиска: Сервис временно заблокирован или требуется CAPTCHA. Попробуйте изменить запрос. ({e})"
        }), 500
    except Exception as e:
        # Обработка других ошибок
         print(f"ЛОГ БЭКЕНДА: Неизвестная ошибка: {e}")
         return jsonify({"status": "error", "message": "Произошла неизвестная ошибка на сервере API."}, 500)


    # Возвращаем успешный ответ
    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    
    return jsonify({
        "status": "success",
        "query": query_ru, 
        "execution_time_seconds": execution_time,
        "results_count": len(results),
        "results": results
    }), 200
