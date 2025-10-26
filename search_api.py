from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import time
import json # Для использования JSON.dumps

# Инициализация приложения Flask
app = Flask(__name__)
# Включаем CORS, чтобы при локальной разработке не было проблем с запросами
CORS(app)

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
        
    # Сортируем по цене, как требует фронтенд
    mockData.sort(key=lambda x: x['price'])
    return mockData


# API маршрут для обработки POST-запросов поиска
@app.route('/api/search', methods=['POST'])
def search_catalog():
    # 1. Обработка входящего JSON
    try:
        data = request.get_json()
    except Exception:
        # 400 Bad Request
        return jsonify({"error": "Не удалось распарсить JSON-тело запроса."}), 400

    # 2. Извлекаем массив 'queries'
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


# --- КОРНЕВОЙ МАРШРУТ, ВОЗВРАЩАЮЩИЙ HTML-ФРОНТЕНД ---
@app.route('/')
def index():
    # Используем тройные кавычки для удобства вставки большого блока HTML/JS
    HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PSP Оборудование: Поиск по Интернет-Источникам</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Настройки шрифта Inter для всего документа */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6;
        }
        /* Стиль для карточки - темный фон и тень при наведении, как требуется */
        .equipment-card {
            background-color: #111827; /* Темно-серый */
            color: white;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        .equipment-card:hover {
            transform: translateY(-5px); /* Поднятие */
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
        }
        /* Стили для мобильных устройств */
        @media (max-width: 640px) {
            .container {
                padding: 0.5rem;
            }
        }
        .loading-animation {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid #4f46e5;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="min-h-screen">
    
    <div class="container mx-auto p-4 md:p-8">

        <!-- Заголовок -->
        <header class="text-center mb-10">
            <h1 class="text-4xl font-extrabold text-gray-800">PSP Агрегатор Поиска Оборудования</h1>
            <p class="text-gray-600 mt-2">Единый поиск по интернет-источникам РФ и СНГ</p>
        </header>

        <!-- Поисковая Форма -->
        <div class="max-w-3xl mx-auto bg-white p-6 rounded-xl shadow-lg mb-8">
            <form id="search-form" class="flex flex-col sm:flex-row gap-4">
                <input 
                    type="text" 
                    id="search-input" 
                    placeholder="Введите название оборудования (напр., Shure SM58)"
                    required
                    class="flex-grow p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-150"
                >
                <button 
                    type="submit"
                    id="search-button"
                    class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition duration-150 ease-in-out disabled:bg-indigo-400"
                >
                    Найти
                </button>
            </form>

            <!-- Фильтры -->
            <div class="mt-4 flex flex-col md:flex-row items-center gap-4">
                <label for="price-filter-min" class="text-gray-700 whitespace-nowrap">Цена от:</label>
                <input type="number" id="price-filter-min" placeholder="Мин. цена (₽)" class="w-full md:w-auto p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500">
                
                <label for="price-filter-max" class="text-gray-700 whitespace-nowrap">Цена до:</label>
                <input type="number" id="price-filter-max" placeholder="Макс. цена (₽)" class="w-full md:w-auto p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500">
                
                <button 
                    id="apply-filters-button"
                    class="w-full md:w-auto bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-150"
                >
                    Применить
                </button>
            </div>
        </div>

        <!-- Сообщения и Индикатор Загрузки -->
        <div id="status-message" class="text-center text-lg font-medium mb-6 min-h-6"></div>
        <div id="loading-indicator" class="flex justify-center items-center mb-6 hidden">
            <div class="loading-animation"></div>
        </div>

        <!-- Контейнер для Результатов Поиска -->
        <div id="results-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Здесь будут отображаться карточки товаров -->
        </div>

        <!-- Пагинация -->
        <div id="pagination-container" class="flex justify-center items-center mt-8 gap-4 hidden">
            <button id="prev-page-button" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg transition duration-150 disabled:opacity-50">
                Назад
            </button>
            <span id="page-info" class="text-gray-700 font-medium">Страница 1 из 4</span>
            <button id="next-page-button" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg transition duration-150 disabled:opacity-50">
                Вперед
            </button>
        </div>

    </div>

    <script>
        // Глобальные переменные для хранения состояния
        let allResults = [];
        let filteredResults = [];
        let currentPage = 1;
        const ITEMS_PER_PAGE = 5; // Согласно правилам
        const MAX_RETRIES = 6; // Максимальное количество попыток для fetch
        const API_URL = '/api/search'; // Относительный URL для API

        // --- DOM Элементы ---
        const searchForm = document.getElementById('search-form');
        const searchInput = document.getElementById('search-input');
        const searchButton = document.getElementById('search-button');
        const resultsContainer = document.getElementById('results-container');
        const statusMessage = document.getElementById('status-message');
        const loadingIndicator = document.getElementById('loading-indicator');
        const paginationContainer = document.getElementById('pagination-container');
        const prevPageButton = document.getElementById('prev-page-button');
        const nextPageButton = document.getElementById('next-page-button');
        const pageInfo = document.getElementById('page-info');
        const applyFiltersButton = document.getElementById('apply-filters-button');
        const priceFilterMin = document.getElementById('price-filter-min');
        const priceFilterMax = document.getElementById('price-filter-max');

        // --- УТИЛИТЫ ---

        /**
         * Рендерит одну карточку товара.
         * @param {object} item - Объект товара.
         * @returns {string} HTML-строка карточки.
         */
        function renderCard(item) {
            const isRankOne = item.rank === 1;
            const rankBadge = isRankOne 
                ? '<span class="absolute top-2 right-2 bg-yellow-500 text-gray-900 text-xs font-bold px-3 py-1 rounded-full shadow-lg">Топ Цена</span>'
                : '';
            
            return `
                <a href="${item.uri}" target="_blank" class="equipment-card p-5 rounded-xl shadow-md relative block">
                    ${rankBadge}
                    <h2 class="text-xl font-semibold mb-2">${item.title}</h2>
                    <p class="text-gray-300 text-sm mb-4">${item.snippet}</p>
                    <div class="flex justify-between items-center border-t border-gray-700 pt-3">
                        <div class="text-2xl font-extrabold text-green-400">
                            ${item.price.toLocaleString('ru-RU')} ₽
                        </div>
                        <span class="text-sm font-medium text-indigo-400">${item.source}</span>
                    </div>
                </a>
            `;
        }

        /**
         * Отображает текущую страницу результатов.
         */
        function renderPage() {
            const start = (currentPage - 1) * ITEMS_PER_PAGE;
            const end = start + ITEMS_PER_PAGE;
            const pageItems = filteredResults.slice(start, end);

            resultsContainer.innerHTML = pageItems.map(renderCard).join('');
            
            const totalPages = Math.ceil(filteredResults.length / ITEMS_PER_PAGE);

            // Обновление пагинации
            pageInfo.textContent = \`Страница \${currentPage} из \${totalPages || 1}\`;
            prevPageButton.disabled = currentPage === 1;
            nextPageButton.disabled = currentPage >= totalPages;
            
            if (filteredResults.length > 0) {
                paginationContainer.classList.remove('hidden');
            } else {
                paginationContainer.classList.add('hidden');
            }

            // Прокрутка к началу результатов для удобства
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // --- ЛОГИКА ФИЛЬТРАЦИИ И СОРТИРОВКИ ---

        /**
         * Применяет фильтры и сортировку к результатам.
         */
        function applyFiltersAndSort() {
            const min = parseFloat(priceFilterMin.value) || 0;
            const max = parseFloat(priceFilterMax.value) || Infinity;

            // 1. Фильтрация
            filteredResults = allResults.filter(item => {
                return item.price >= min && item.price <= max;
            });

            // 2. Сортировка по возрастанию цены (делаем это на фронтенде, 
            // так как API заглушка это уже делает, но на всякий случай)
            filteredResults.sort((a, b) => a.price - b.price);

            // Сброс на первую страницу после фильтрации
            currentPage = 1;
            renderPage();

            statusMessage.className = "text-center text-lg font-medium mb-6";
            if (allResults.length === 0) {
                 statusMessage.textContent = 'Введите запрос для начала поиска.';
            } else if (filteredResults.length === 0) {
                 statusMessage.textContent = 'Нет результатов, соответствующих заданным фильтрам.';
                 resultsContainer.innerHTML = '';
            } else {
                 statusMessage.textContent = \`Найдено \${allResults.length} результатов. Показано \${filteredResults.length} после фильтрации.\`;
                 statusMessage.classList.add('text-gray-700');
            }
        }

        // --- ЛОГИКА API ЗАПРОСОВ ---

        /**
         * Выполняет POST-запрос к API с логикой экспоненциального повтора.
         * @param {Array<string>} queries - Массив запросов.
         */
        async function fetchSearchResults(queries) {
            searchButton.disabled = true;
            loadingIndicator.classList.remove('hidden');
            statusMessage.textContent = 'Ищем предложения...';
            statusMessage.classList.remove('text-red-500', 'text-green-500');
            statusMessage.classList.add('text-indigo-600');
            resultsContainer.innerHTML = '';
            paginationContainer.classList.add('hidden');
            
            const payload = { queries: queries };
            
            for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(payload),
                    });

                    // Проверяем статус ответа
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(\`Сервер вернул ошибку (\${response.status}): \${errorData.error || response.statusText}\`);
                    }

                    const data = await response.json();
                    
                    // Успех
                    allResults = data.results || [];
                    
                    // Применяем фильтры и рендерим (сортировка происходит внутри applyFiltersAndSort)
                    applyFiltersAndSort(); 

                    loadingIndicator.classList.add('hidden');
                    searchButton.disabled = false;
                    statusMessage.classList.remove('text-red-500', 'text-indigo-600');
                    statusMessage.classList.add('text-green-600');
                    if (allResults.length > 0) {
                         statusMessage.textContent = \`Поиск завершен! Найдено \${allResults.length} результатов.\`;
                    } else {
                         statusMessage.textContent = 'Поиск завершен. К сожалению, ничего не найдено.';
                         resultsContainer.innerHTML = '';
                    }
                    return; // Выходим из цикла при успехе

                } catch (error) {
                    const baseDelay = 1000; // 1 секунда
                    const delay = baseDelay * Math.pow(2, attempt - 1); // Экспоненциальная задержка
                    
                    if (attempt < MAX_RETRIES) {
                        statusMessage.textContent = \`Попытка \${attempt} из \${MAX_RETRIES} не удалась. Повтор через \${(delay / 1000).toFixed(1)} сек...\`;
                        console.error(\`Ошибка API (\${attempt}):\`, error.message);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    } else {
                        // Последняя попытка не удалась
                        loadingIndicator.classList.add('hidden');
                        searchButton.disabled = false;
                        statusMessage.classList.remove('text-indigo-600', 'text-green-600');
                        statusMessage.classList.add('text-red-500');
                        statusMessage.textContent = \`Поиск не удался после \${MAX_RETRIES} попыток. \${error.message}\`;
                        console.error('Критическая ошибка API:', error);
                    }
                }
            }
        }

        // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

        // Обработка отправки формы
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                // В данной заглушке не требуется перевод, просто передаем один запрос
                fetchSearchResults([query]);
            }
        });

        // Обработка пагинации
        prevPageButton.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderPage();
            }
        });

        nextPageButton.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredResults.length / ITEMS_PER_PAGE);
            if (currentPage < totalPages) {
                currentPage++;
                renderPage();
            }
        });
        
        // Обработка фильтрации
        applyFiltersButton.addEventListener('click', applyFiltersAndSort);
        // Также можно применить фильтры при нажатии Enter в полях
        priceFilterMin.addEventListener('keypress', (e) => { if (e.key === 'Enter') applyFiltersAndSort(); });
        priceFilterMax.addEventListener('keypress', (e) => { if (e.key === 'Enter') applyFiltersAndSort(); });
        
        // Инициализация при загрузке страницы
        window.onload = () => {
            statusMessage.textContent = 'Введите запрос для начала поиска.';
            statusMessage.classList.add('text-gray-700');
        }

    </script>
</body>
</html>
"""
    return HTML_CONTENT

if __name__ == '__main__':
    # Для локального запуска
    print("Запуск Flask-сервера...")
    app.run(debug=True, port=5000)
