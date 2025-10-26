from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import random
import time
import re
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import requests 

# Инициализация приложения Flask
app = Flask(__name__)
CORS(app) 

# --- КОНСТАНТЫ ДЛЯ РЕАЛЬНОГО (НО ОГРАНИЧЕННОГО) ПОИСКА ---
SEARCH_URL_RU = "https://www.google.com/search?hl=ru&gl=ru&q="
SEARCH_URL_EN = "https://www.google.com/search?hl=en&gl=us&q=" # Для двуязычности
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SOURCE_OPTIONS = ["Яндекс.Маркет", "Ozon", "MusicStore.ru", "Avito Pro", "ProAudioStore", "DJEquipment"] # Расширенный список

# --- СТАТИЧНЫЕ КАТЕГОРИИ (ДОБАВЛЕНО ПО ЗАПРОСУ ПОЛЬЗОВАТЕЛЯ) ---
CATEGORIES = [
    "DJ-оборудование", "Акустические системы", "Запасные части", "Коммутация (кабели и разъёмы)",
    "Компьютерные аудиоинтерфейсы и контроллеры", "Конференционные системы", "Микрофоны", "Микшеры",
    "Музыкальные инструменты и оборудование", "Наушники и усилители для наушников",
    "Обработка и преобразование сигналов", "Программное обеспечение", "Проигрыватели, рекордеры, FM/AM тюнеры",
    "Радиосистемы", "Световое оборудование", "Системы персонального мониторинга",
    "Стойки, чехлы, рэки", "Студийные мониторы и сабвуферы", "Усилители", "Уцененное оборудование",
    "Семпл-образец"
]

# --- ФУНКЦИИ БЕЗОПАСНОГО ВЕБ-СКАЧИВАНИЯ ---

def get_page_content(uri: str) -> str | None:
    """
    Безопасно загружает содержимое страницы по URI. 
    Устанавливает таймаут, чтобы избежать зависаний.
    """
    try:
        # Имитируем задержку для загрузки страницы, чтобы показать, что это реальная операция
        time.sleep(random.uniform(0.1, 0.5))
        
        # В реальном приложении здесь был бы:
        # response = requests.get(uri, headers={'User-Agent': USER_AGENT}, timeout=3)
        # response.raise_for_status()
        # return response.text
        
        # Для симуляции: просто возвращаем заглушку
        print(f"ЛОГ БЭКЕНДА: Имитация загрузки страницы: {uri}")
        return "<html><body>Mock Content</body></html>" 
        
    except RequestException as e:
        print(f"ЛОГ БЭКЕНДА: Ошибка при загрузке URI {uri}: {e}")
        return None

# --- ФУНКЦИИ ИЗВЛЕЧЕНИЯ ДАННЫХ ИЗ КОНТЕНТА ---

def extract_price_and_title(html_content: str, uri: str) -> dict:
    """
    Имитирует извлечение точной цены, названия и источника 
    непосредственно из контента страницы (второй этап).
    
    В реальном проекте: использовался бы BeautifulSoup для парсинга HTML, 
    но здесь мы используем имитацию для демонстрации логики.
    """
    
    # 1. Извлечение/Генерация Цены: 
    # Генерируем цену на основе URI (имитируя, что цена зависит от магазина)
    uri_hash = sum(ord(c) for c in uri)
    
    # Случайный, но детерминированный диапазон цен
    price_base = (uri_hash % 50000) + 10000
    price_deviation = random.randint(-5000, 5000)
    price = max(10000, price_base + price_deviation)

    # 2. Определение Источника (Source):
    # Извлекаем домен, чтобы получить имя магазина
    try:
        domain = re.search(r'(?:https?:\/\/)?(?:www\.)?([^/]+)', uri).group(1)
        # Делаем источник более дружелюбным
        if 'yandex' in domain:
            source = 'Яндекс.Маркет'
        elif 'ozon' in domain:
            source = 'Ozon'
        elif 'musicstore' in domain:
            source = 'MusicStore.ru'
        else:
            # Случайное присвоение из списка, чтобы не было слишком много одинаковых
            source = random.choice(SOURCE_OPTIONS)
    except:
        source = random.choice(SOURCE_OPTIONS)

    # 3. Извлечение/Генерация Названия:
    # Предполагаем, что название товара на странице более точное
    # Имитируем добавление артикула или точного названия модели
    mock_title = f"Товар (Арт. {uri_hash % 9999}) в наличии - {source}"

    return {
        "price": price,
        "source": source,
        "title_override": mock_title # Используем для замены общего заголовка
    }


def extract_initial_search_results(soup: BeautifulSoup) -> list:
    """
    Парсит HTML-суп для извлечения заголовков, сниппетов и ссылок (Первый этап).
    Возвращает список словарей: [{'title', 'snippet', 'uri'}]
    """
    
    # В реальном поиске Google нужно искать специфичные CSS-классы или структуры.
    # Мы имитируем этот процесс, возвращая псевдо-результаты, которые будут
    # использованы для второго этапа парсинга.
    
    results = []
    
    # Имитация получения 30 ссылок для последующей фильтрации и сокращения до 20
    for i in range(30): 
        # Генерация уникального URI для имитации ссылок на товары
        mock_uri = f"https://example.com/product/{random.randint(10000, 99999)}/q={i}"
        
        # Добавляем дубликаты, чтобы показать работу deduplication
        if i % 5 == 0 and i > 0:
            mock_uri = results[-1]['uri'] # Дублируем предыдущий URI
            
        results.append({
            "title": f"Имитация: Найденный результат №{i+1}",
            "snippet": f"Краткое описание товара или категории. Поиск был инициирован.",
            "uri": mock_uri, 
        })
        
    return results


def perform_google_search(query_ru: str, query_en: str) -> list:
    """
    Выполняет два этапа поиска:
    1. Имитация получения ссылок от Google (двуязычный поиск).
    2. Имитация перехода по каждой ссылке для уточнения данных.
    3. Очистка, сортировка и ранжирование.
    """
    print(f"ЛОГ БЭКЕНДА: Начало двухэтапного поиска. RU: '{query_ru}', EN: '{query_en}'")
    
    # --- ЭТАП 1: Первичный поиск и сбор URI ---
    
    # В реальном приложении здесь было бы два запроса (RU и EN) и объединение результатов.
    # Для имитации: делаем один запрос к RU и получаем mock-данные.
    
    try:
        # Имитируем запрос к Google
        response = requests.get(SEARCH_URL_RU + query_ru, headers={'User-Agent': USER_AGENT}, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        initial_results = extract_initial_search_results(soup)
        
    except RequestException as e:
        print(f"ЛОГ БЭКЕНДА: Ошибка на этапе 1 (Google): {e}")
        # Возвращаем пустые данные для продолжения, если первый этап не удался
        initial_results = [] 
    
    if not initial_results:
        print("ЛОГ БЭКЕНДА: Этап 1 не дал результатов.")
        return []
        
    # --- ЭТАП 2: Уточнение данных по URI и дедупликация (ВЫГРУЗКА И СКАНИРОВАНИЕ) ---
    
    unique_uri_map = {} # Используем словарь для дедупликации по URI
    
    for item in initial_results:
        uri = item['uri']
        if uri not in unique_uri_map:
            
            # Получаем контент страницы (имитация)
            html_content = get_page_content(uri) 
            
            if html_content:
                # Извлекаем точные данные со страницы
                page_data = extract_price_and_title(html_content, uri)
                
                # Объединяем первичные и уточненные данные
                final_item = {
                    "id": len(unique_uri_map) + 1,
                    "title": page_data['title_override'],  # Используем более точный title
                    "snippet": item['snippet'],
                    "uri": uri,
                    "source": page_data['source'],
                    "price": page_data['price'],
                    "rank": 0,
                }
                unique_uri_map[uri] = final_item
                
    # Преобразуем словарь обратно в список и сокращаем до 20 (Правило 2.4.a)
    refined_results = list(unique_uri_map.values())[:20]
    
    if not refined_results:
         print("ЛОГ БЭКЕНДА: Не удалось получить 20 уникальных, уточненных результатов.")
         return []

    # --- ЭТАП 3: Сортировка и Ранжирование ---

    # Сортируем по цене (по возрастанию)
    refined_results.sort(key=lambda x: x['price'])
    
    # Устанавливаем ранг 1 для лучшего (самого дешевого) предложения
    if refined_results:
        refined_results[0]['rank'] = 1 
        print(f"ЛОГ БЭКЕНДА: Лучшее предложение: {refined_results[0]['title']} за {refined_results[0]['price']} ₽")
    
    print(f"ЛОГ БЭКЕНДА: Возвращается {len(refined_results)} отсортированных результатов после двух этапов.")
    return refined_results


# --- API МАРШРУТ ---

# Маршрут доступен как GET (для проверки), так и POST (для реальной работы)
@app.route('/api/search', methods=['GET', 'POST'])
def search_catalog():
    start_time = time.time()
    
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
        return jsonify({"status": "error", "message": "Не удалось распарсить JSON-тело запроса."}), 400

    # 2. Извлекаем массив 'queries', который отправляет фронтенд
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        return jsonify({
            "status": "error",
            "message": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк."
        }), 400

    # Используем первый запрос из массива (русский)
    query_ru = queries[0]
    # Используем второй запрос из массива (английский)
    query_en = queries[1] if len(queries) > 1 else query_ru

    
    # 3. Вызываем функцию "реального" поиска
    try:
        # Запускаем двухэтапный поиск
        results = perform_google_search(query_ru, query_en)
        
    except RequestException as e:
        # Обработка ошибок, связанных с внешними запросами 
        print(f"ЛОГ БЭКЕНДА: Критическая ошибка сети при выполнении поиска: {e}")
        return jsonify({"status": "error", "message": f"Критическая ошибка сети при подключении к поисковому сервису: {e}"}), 500


    # 4. Возвращаем успешный ответ
    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    
    return jsonify({
        "status": "success",
        "query": query_ru, # Возвращаем русский запрос
        "execution_time_seconds": execution_time,
        "results_count": len(results),
        "results": results
    }), 200
