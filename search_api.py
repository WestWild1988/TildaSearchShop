import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# ==============================================================================
# КОНСТАНТЫ
# ==============================================================================

# Таймаут для каждого запроса на скрапинг отдельной страницы
SCRAPE_TIMEOUT = 5
MAX_LINKS_TO_SCRAPE = 5 # Ограничиваем количество скрапируемых ссылок для демонстрации
BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ==============================================================================
# ЭТАП 1: ПОЛУЧЕНИЕ ССЫЛОК (ИМИТАЦИЯ ВНЕШНЕГО ПОИСКА)
# ==============================================================================

def get_search_links(query: str) -> list[str]:
    """
    Имитирует вызов внешнего поисковика (Яндекс/Google) для получения 
    списка релевантных ссылок.

    В реальном приложении здесь будет логика вызова поискового API.
    Пока возвращаем захардкоженные ссылки для тестирования Этапа 2.
    """
    print(f"[{os.getpid()}] ЭТАП 1: Выполняется имитация поиска для запроса: {query}")
    
    # В реальном коде:
    # 1. Сформировать запрос (например, 'микрофон Sennheiser купить')
    # 2. Вызвать Google/Яндекс Search API
    # 3. Вернуть список URIs (до 20 штук)

    # Демонстрационный список URIs (разные сайты и типы страниц):
    sample_links = [
        "https://pagesound.ru/catalog/dj_oborudovanie/", # Каталог
        "https://www.pop-music.ru/products/shure-sm58-lce-541/", # Страница товара 1
        "https://pro-audio.ru/catalog/besprovodnye-mikrofonnye-sistemy/besprovodnaya-mikrofonnaya-sistema-sennheiser-ew-100-g4-835-s/", # Страница товара 2
        "https://muz.by/catalog/usiliteli-moshchnosti/roland-s1000-850w/", # Страница товара 3 (другой сайт)
        "https://www.avito.ru/moskva/muzykalnye_instrumenty/mikrofon_besprovodnoy_sennheiser_988771234", # Страница товара с Авито (для демонстрации сбоя/разнообразия)
        "https://pagesound.ru/catalog/mikrofony/", # Еще одна ссылка из Pagesound
    ]
    
    # Имитируем, что запрос "Sennheiser" дает более релевантный набор
    if 'sennheiser' in query.lower():
        return sample_links[:4] # Более релевантные ссылки
    
    # Возвращаем первые MAX_LINKS_TO_SCRAPE для тестирования
    return sample_links[:MAX_LINKS_TO_SCRAPE]


# ==============================================================================
# ЭТАП 2: СКРАПИНГ ОТДЕЛЬНОЙ СТРАНИЦЫ
# ==============================================================================

def parse_price(price_text):
    """ Очищает и преобразует текст цены в числовое значение и форматированный вид. """
    if not price_text:
        return None, "Цена не указана"
    clean_price = re.sub(r'[^\d]', '', price_text)
    try:
        value = int(clean_price)
        formatted_price = f"{value:,}".replace(',', ' ') + ' ₽'
        return value, formatted_price
    except ValueError:
        return None, price_text.strip()

def scrape_product_page(url: str) -> dict or None:
    """
    Парсит отдельную страницу по универсальным селекторам для извлечения 
    данных о товаре (карточке).
    """
    print(f"[{os.getpid()}] ЭТАП 2: Скрапинг страницы: {url}")

    try:
        response = requests.get(url, headers=BASE_HEADERS, timeout=SCRAPE_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. TITLE - Поиск по H1 или OpenGraph (самый надежный)
        title_tag = soup.select_one('h1') or soup.select_one('.product-title')
        title = title_tag.get_text(strip=True) if title_tag else "Название не найдено"
        
        # 2. PRICE - Поиск по общим селекторам цены
        price_tag = soup.select_one('.price__value') or soup.select_one('.product-price-value') or soup.select_one('.item__price')
        price_raw = price_tag.get_text(strip=True) if price_tag else "Цена не указана"
        price_value, price_display = parse_price(price_raw)
        
        # 3. IMAGE - Поиск по OpenGraph или основному изображению
        og_image = soup.find('meta', property='og:image')
        img_url = og_image['content'] if og_image and og_image.get('content') else None

        if not img_url:
            main_img_tag = soup.select_one('.main-image img') or soup.select_one('.item__img img')
            if main_img_tag and main_img_tag.get('src'):
                 # Преобразуем относительный путь в абсолютный, если нужно
                img_url = main_img_tag['src']
                if img_url.startswith('/'):
                    parsed_url = urlparse(url)
                    img_url = f"{parsed_url.scheme}://{parsed_url.netloc}{img_url}"

        if not img_url:
            img_url = 'https://placehold.co/150x150/500000/FFFFFF?text=No+Image'
        
        # 4. SNIPPET - Описание
        description_meta = soup.find('meta', attrs={'name': 'description'})
        snippet_text = description_meta['content'] if description_meta and description_meta.get('content') else "Краткое описание отсутствует."

        # 5. SOURCE DOMAIN
        source_domain = urlparse(url).netloc

        # Фильтр для нерелевантных страниц (например, если нет цены и название не похоже на товар)
        if price_value is None and "название не найдено" in title.lower():
             print(f"[{os.getpid()}] ЭТАП 2: Страница не похожа на товар. Пропуск.")
             return None

        return {
            "id": f"scraped-{hash(url)}", # Используем хэш URL для уникального ID
            "title": title,
            "snippet": snippet_text[:200] + '...' if len(snippet_text) > 200 else snippet_text, # Ограничиваем длину
            "uri": url,
            "source_domain": source_domain,
            "image_url": img_url,
            "price_value": price_value,
            "price_raw": price_display,
        }

    except requests.exceptions.RequestException as e:
        print(f"[{os.getpid()}] Ошибка запроса к {url}: {e}")
        return None
    except Exception as e:
        print(f"[{os.getpid()}] Общая ошибка при скрапинге {url}: {e}")
        return None


# ==============================================================================
# ОРКЕСТРАТОР: УПРАВЛЕНИЕ ДВУМЯ ЭТАПАМИ
# ==============================================================================

def two_stage_search(query: str):
    """
    Выполняет двухэтапный поиск: 
    1. Получает ссылки через поисковик.
    2. Скрапит каждую ссылку.
    """
    
    # 1. ЭТАП 1: Получаем список ссылок
    search_links = get_search_links(query)
    
    final_results = []
    
    # 2. ЭТАП 2: Последовательно скрапим каждую ссылку
    for url in search_links:
        # Ограничиваем количество, чтобы избежать слишком долгой работы
        if len(final_results) >= MAX_LINKS_TO_SCRAPE:
            break
            
        product_data = scrape_product_page(url)
        
        if product_data:
            final_results.append(product_data)
            
    # 3. Возвращаем результат
    if not final_results:
        return {"error": f"Ничего не найдено после двухэтапного поиска по запросу: {query}"}, 404
            
    return final_results, 200


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
    
    # 1. Выполняем логику двухэтапного поиска
    results, status_code = two_stage_search(query)
    
    # 2. Возвращаем результат
    return jsonify(results), status_code

# Добавляем маршрут для проверки работоспособности (health check)
@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервиса.
    """
    return jsonify({"status": "ok", "service": "psp-search-backend (Two-Stage Scraping)", "search_engine": "BeautifulSoup"}), 200


if __name__ == '__main__':
    # Эта часть не используется в продакшене, но нужна для локального запуска
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
