# search_api.py
#
# Скрипт бэкенда для Tilda Live Search, развернутый на Render.
# Использует FastAPI для приема запросов и BeautifulSoup для скрейпинга Google.

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Dict, Any

# ==============================================================================
# 1. НАСТРОЙКА FASTAPI И МОДЕЛИ ДАННЫХ
# ==============================================================================

app = FastAPI(
    title="Tilda Search Shop API",
    description="API для выполнения умного поиска по Интернету с использованием скрейпинга Google.",
    version="1.0.0"
)

# Модель для входных данных (должна совпадать с фронтендом Tilda)
class SearchQuery(BaseModel):
    # Ожидаем одну детализированную строку запроса, сгенерированную на Tilda.
    query: str

# Заголовки для имитации браузера Chrome (повышает шансы на успешный скрейпинг)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# Максимальное количество результатов, которое мы пытаемся получить (20-25)
MAX_RESULTS_TARGET = 25 

# Базовый URL для поиска Google
GOOGLE_SEARCH_URL = "https://www.google.com/search"

# ==============================================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

def scrape_google(query: str, num_results: int = 100) -> List[Dict[str, str]]:
    """
    Выполняет скрейпинг поисковой выдачи Google для получения структурированных результатов.

    :param query: Детализированный поисковый запрос.
    :param num_results: Максимальное количество результатов для поиска.
    :return: Список словарей с title, snippet и uri.
    """
    
    results = []
    # Параметры: q=запрос, num=количество результатов на странице, start=смещение.
    params = {'q': query, 'hl': 'ru', 'num': min(num_results, 100)} # Google ограничивает num до 100
    
    try:
        # Отправляем запрос с имитацией заголовков браузера
        response = requests.get(GOOGLE_SEARCH_URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status() # Вызывает исключение для плохих статусов (4xx, 5xx)

        # Проверка на reCAPTCHA или блокировку (хотя это не 100% гарантия)
        if "recaptcha" in response.text.lower() or "обнаружен автоматический запрос" in response.text.lower():
             print("ПРЕДУПРЕЖДЕНИЕ: Обнаружена reCAPTCHA или блокировка Google.")
             return [{"title": "Ошибка скрейпинга: Блокировка Google", 
                      "snippet": "Google заблокировал запрос. Попробуйте изменить запрос или повторить позже.",
                      "uri": "#error"}]

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все блоки результатов. Классы могут меняться!
        # Используем несколько распространенных селекторов для повышения надежности:
        result_blocks = soup.find_all('div', class_='tF2C2f') # Основной блок результатов
        if not result_blocks:
             result_blocks = soup.find_all('div', class_='g') # Более общий класс

        for block in result_blocks:
            # 1. Находим заголовок и URL (тег <a> с классом в заголовке)
            link_tag = block.find('a')
            if not link_tag:
                continue
            
            # Извлекаем URL
            uri = link_tag.get('href')
            # Извлекаем заголовок (обычно в теге <h3> внутри <a>)
            title_tag = link_tag.find('h3')
            title = title_tag.get_text() if title_tag else "Название не найдено"
            
            # 2. Находим сниппет (описание)
            # Сниппет может быть в div, span или просто текстом после заголовка.
            # Попробуем найти тег span с классом, содержащим описание (сниппет)
            snippet_tag = block.find('span', class_='aCOpRe') # Один из распространенных классов
            if not snippet_tag:
                 # Ищем сниппет в общем блоке, пропуская h3
                snippet_tag = block.find('div', class_='VwiC3b') # Другой класс
                
            snippet = snippet_tag.get_text() if snippet_tag else "Описание (сниппет) не найдено."

            results.append({
                "title": title,
                "snippet": snippet,
                "uri": uri
            })
            
            # Если достигли целевого количества, останавливаемся
            if len(results) >= MAX_RESULTS_TARGET:
                 break
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при HTTP-запросе к Google: {e}")
        return [{"title": "Критическая ошибка HTTP", 
                 "snippet": f"Не удалось подключиться к Google: {e}",
                 "uri": "#critical-error"}]
        
    return results

# ==============================================================================
# 3. ЭНДПОИНТ API
# ==============================================================================

@app.post("/api/search", response_model=List[Dict[str, str]])
async def search_backend(query_data: SearchQuery):
    """
    Принимает поисковый запрос от Tilda, выполняет скрейпинг Google 
    и возвращает список результатов.
    """
    query = query_data.query.strip()
    
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Поисковый запрос не может быть пустым."
        )

    print(f"Получен запрос: {query}")

    # Выполняем скрейпинг
    scraped_results = scrape_google(query, MAX_RESULTS_TARGET)
    
    if not scraped_results or scraped_results[0].get("uri") == "#error":
        # Если скрейпинг не дал результатов или вернул ошибку, 
        # возвращаем пустой список, чтобы Tilda отобразила "ничего не найдено".
        return JSONResponse(content=scraped_results if scraped_results else [], status_code=200)

    # Добавляем фиктивные/дублирующие результаты, если их меньше 25, 
    # чтобы Tilda могла корректно отобразить пагинацию (5 страниц).
    # В реальном проекте, конечно, лучше найти 25.
    
    final_results = scraped_results
    if len(final_results) < MAX_RESULTS_TARGET:
        print(f"Найдено только {len(final_results)} результатов. Добавляем дубликаты.")
        
        while len(final_results) < MAX_RESULTS_TARGET:
            # Циклически дублируем, чтобы добрать нужное количество (для теста пагинации)
            for item in scraped_results:
                # Создаем копию с небольшим изменением title, чтобы избежать полного дублирования
                new_item = item.copy()
                new_item["title"] = f"{item['title']} (копия {len(final_results)+1})"
                final_results.append(new_item)
                if len(final_results) >= MAX_RESULTS_TARGET:
                    break
    
    # Обрезаем до 25 (если дублирование превысило цель)
    final_results = final_results[:MAX_RESULTS_TARGET]
    
    print(f"Возврат {len(final_results)} результатов.")
    return JSONResponse(content=final_results, status_code=200)

# ==============================================================================
# 4. НАСТРОЙКА CORS (Обязательно для работы между Tilda и Render)
# ==============================================================================
from fastapi.middleware.cors import CORSMiddleware

# В боевой среде нужно указать точный домен Tilda, например: https://tildasearchshop.tilda.ws
# Для тестирования указываем '*' (все домены)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене: ["https://tildasearchshop.tilda.ws"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Для запуска локально используйте: uvicorn search_api:app --reload
