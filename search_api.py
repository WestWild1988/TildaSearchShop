import json
from typing import List, Dict, Any, Union
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# --------------------------------------------------------------------------------
# 1. ИМПОРТ ИНСТРУМЕНТА ПОИСКА (ПРЕДПОЛАГАЕТСЯ НАЛИЧИЕ В ПРОД. СРЕДЕ)
# --------------------------------------------------------------------------------
# При развертывании на Render, этот импорт будет работать, если API имеет доступ
# к инструменту Google Search.
try:
    from google_search import search
    # Флаг для определения, используется ли реальный поиск или заглушка
    REAL_SEARCH_ACTIVE = True 
except ImportError:
    # Заглушка (MOCK) для локального тестирования или среды без инструмента
    print("ВНИМАНИЕ: Инструмент 'google_search' не найден. Активирована локальная ЗАГЛУШКА.")
    REAL_SEARCH_ACTIVE = False
    
    # Имитация функции search для локального тестирования
    def search(queries: List[str]) -> List[Dict[str, Any]]:
        return [
            {"title": f"MOCK Result {i+1} ({queries[0][:20]}...)", 
             "snippet": f"Имитация данных: Найден релевантный сниппет для запроса.", 
             "uri": f"https://mock.example.com/item/{i}"} 
            for i in range(15)
        ]
        
# --------------------------------------------------------------------------------
# 2. СТРУКТУРЫ ДАННЫХ
# --------------------------------------------------------------------------------

# Модель входящего запроса (соответствует payload из search_interface.html)
class SearchRequest(BaseModel):
    queries: List[str]

# Модель исходящего результата (формат для карточек в HTML)
class SearchResult(BaseModel):
    title: str
    snippet: str
    uri: str

# --------------------------------------------------------------------------------
# 3. НАСТРОЙКА FASTAPI И CORS
# --------------------------------------------------------------------------------

app = FastAPI(
    title="PSP Equipment Search API (Production Ready)",
    description="API для выполнения поиска по аудиооборудованию с реальным Google Search (или MOCK).",
    version="1.0.0"
)

# Настройка CORS: разрешаем запросы со всех доменов, включая ваш фронтенд на Тильде
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем запросы откуда угодно
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------
# 4. ФУНКЦИЯ ВЫПОЛНЕНИЯ ПОИСКА
# --------------------------------------------------------------------------------

async def run_search_queries(queries: List[str]) -> List[SearchResult]:
    """
    Выполняет поиск, дедупликацию и форматирование результатов.
    Логика взята из проверенного консольного скрипта.
    """
    if not queries:
        return []

    # Если заглушка, добавляем небольшую задержку для имитации сети
    if not REAL_SEARCH_ACTIVE:
        await asyncio.sleep(0.5)

    print(f"LOG: Запуск поиска (Реальный: {REAL_SEARCH_ACTIVE}). Запросов: {len(queries)}")
    
    # Выполнение поиска (реального или заглушки)
    search_response = search(queries=queries)
    
    # Обработка, дедупликация и ограничение результатов (до 15)
    unique_results: Dict[str, SearchResult] = {}
    
    for item in search_response:
        uri = item.get("uri", "")
        # Исключаем ссылки, где нет URI
        if uri:
            # Дедупликация по URI
            if uri not in unique_results:
                result_obj = SearchResult(
                    title=item.get("title", "Нет заголовка"),
                    snippet=item.get("snippet", "Нет описания"),
                    uri=uri
                )
                unique_results[uri] = result_obj
            
            # Ограничение до 15 уникальных результатов
            if len(unique_results) >= 15:
                break

    print(f"LOG: Возвращено {len(unique_results)} уникальных результатов.")
    return list(unique_results.values())

# --------------------------------------------------------------------------------
# 5. ЭНДПОЙНТЫ API
# --------------------------------------------------------------------------------

@app.post("/search", response_model=List[SearchResult])
async def search_equipment(request: SearchRequest):
    """
    Основной POST-эндпоинт для приема поисковых запросов от фронтенда.
    """
    if not request.queries:
        raise HTTPException(status_code=400, detail="Запрос должен содержать хотя бы один поисковый критерий.")

    try:
        results = await run_search_queries(request.queries)
        return results
    except Exception as e:
        print(f"ОШИБКА API: {e}")
        # Возвращаем 500 ошибку для фронтенда
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера при выполнении поиска.")

@app.get("/")
def read_root():
    """Простой корневой эндпоинт для проверки работоспособности API."""
    if REAL_SEARCH_ACTIVE:
        return {"status": "ok", "message": "PSP Equipment Search API is running with REAL Google Search."}
    else:
        return {"status": "warning", "message": "PSP Equipment Search API is running with MOCK data."}
