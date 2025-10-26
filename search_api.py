from flask import Flask, request, jsonify, make_response
import random
import time 

# Инициализация приложения Flask
app = Flask(__name__)

# --- HTML-КОД КЛИЕНТСКОГО ПРИЛОЖЕНИЯ ---
# Используем ТРОЙНЫЕ ОДИНАРНЫЕ кавычки (''') для определения HTML_CONTENT, 
# чтобы избежать конфликта с тройными двойными кавычками (""") в JS/HTML.
HTML_CONTENT = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PSP Оборудование: Поиск по Интернет-Источникам</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        /* Настройка шрифта и общие стили */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0d1117; /* Темный фон для всей страницы */
            color: #e5e7eb; /* Светлый текст */
        }
        /* Стиль для карточек результатов */
        .equipment-card {
            background-color: #111827; /* Фон карточки: темно-серый, как в правилах */
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid #2d3748;
        }
        .equipment-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .rank-badge {
            animation: pulse-rank 1.5s infinite;
        }
        @keyframes pulse-rank {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        .no-results {
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 2rem;
            border: 2px dashed #4b5563;
            border-radius: 0.5rem;
            margin-top: 2rem;
        }
        /* Стили для мобильных устройств */
        @media (max-width: 640px) {
            .filters-panel {
                flex-direction: column;
            }
            .filter-group {
                margin-bottom: 1rem;
                width: 100%;
            }
        }
        /* Стили для отладочного окна */
        .debug-panel {
            background-color: #1f2937;
            border: 1px solid #4b5563;
            max-height: 400px;
            overflow-y: auto;
        }
        .debug-code {
            white-space: pre-wrap;
            word-break: break-all;
        }
    </style>
</head>
<body class="min-h-screen">

    <div class="container mx-auto px-4 py-8 max-w-7xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-extrabold text-blue-400 mb-2">PSP Aggregator</h1>
            <p class="text-xl text-gray-400">Поиск сценического, студийного и DJ-оборудования</p>
        </header>

        <!-- Search Form -->
        <div id="search-container" class="mb-8 p-6 bg-gray-800 rounded-xl shadow-2xl">
            <form id="search-form" class="flex flex-col sm:flex-row gap-4">
                <input
                    type="text"
                    id="search-input"
                    placeholder="Например: Shure SM58, Pioneer CDJ-3000..."
                    required
                    class="flex-grow p-3 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500"
                >
                <button
                    type="submit"
                    id="search-button"
                    class="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition duration-200 flex items-center justify-center disabled:opacity-50"
                >
                    <i data-lucide="search" class="w-5 h-5 mr-2"></i> Искать
                </button>
            </form>
        </div>

        <!-- Status and Filters -->
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div id="status-message" class="text-lg font-medium text-gray-300">
                Введите запрос для начала поиска.
            </div>

            <!-- Filter Panel -->
            <div id="filters-panel" class="filters-panel flex flex-wrap gap-4 bg-gray-800 p-4 rounded-lg shadow-md">
                <div class="filter-group">
                    <label for="sort-by" class="text-sm font-medium text-gray-400 block mb-1">Сортировка:</label>
                    <select id="sort-by" class="p-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm">
                        <option value="price_asc">Цена (сначала дешевые)</option>
                        <option value="price_desc">Цена (сначала дорогие)</option>
                        <option value="rank_desc">Рейтинг (сначала лучшие)</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="price-min" class="text-sm font-medium text-gray-400 block mb-1">Мин. Цена (₽):</label>
                    <input type="number" id="price-min" placeholder="0" class="p-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm w-full sm:w-28">
                </div>
                
                <div class="filter-group">
                    <label for="price-max" class="text-sm font-medium text-gray-400 block mb-1">Макс. Цена (₽):</label>
                    <input type="number" id="price-max" placeholder="500000" class="p-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm w-full sm:w-28">
                </div>

                <button id="apply-filters-button" class="mt-auto px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition duration-200 text-sm">
                    Применить
                </button>
            </div>
        </div>

        <!-- Debug Panel -->
        <div class="mt-6 mb-6 p-4 rounded-xl shadow-lg bg-gray-900">
            <h2 class="text-xl font-bold text-red-400 mb-3 flex items-center">
                <i data-lucide="bug" class="w-5 h-5 mr-2"></i> Панель Отладки (Debug)
            </h2>
            <div class="debug-panel p-3 rounded-lg text-sm">
                <p class="font-semibold text-gray-400 mb-2">Переведенные Запросы (queries):</p>
                <code id="debug-queries" class="debug-code text-yellow-300">[]</code>
                
                <p class="font-semibold text-gray-400 mt-4 mb-2">Ответ Сервера (JSON):</p>
                <pre id="debug-response" class="debug-code text-green-300">Ожидание запроса...</pre>
            </div>
        </div>
        
        <!-- Results Grid -->
        <div id="results-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <!-- Search results will be inserted here -->
        </div>

        <!-- Pagination -->
        <div id="pagination-controls" class="flex justify-center items-center gap-4 mt-8">
            <!-- Pagination buttons will be inserted here -->
        </div>
    </div>

    <script>
        // Инициализация Lucide Icons
        lucide.createIcons();

        // --- КОНСТАНТЫ И СОСТОЯНИЕ ---
        // !!! ВАЖНО: API_URL теперь указывает на САМ СЕБЯ, то есть на текущий сервер Render. !!!
        const API_URL = '/api/search'; 
        const RESULTS_PER_PAGE = 5; 
        
        let allResults = []; 
        let filteredResults = []; 
        let currentPage = 1;

        const elements = {
            form: document.getElementById('search-form'),
            input: document.getElementById('search-input'),
            button: document.getElementById('search-button'),
            status: document.getElementById('status-message'),
            grid: document.getElementById('results-grid'),
            pagination: document.getElementById('pagination-controls'),
            sortBy: document.getElementById('sort-by'),
            priceMin: document.getElementById('price-min'),
            priceMax: document.getElementById('price-max'),
            applyFiltersButton: document.getElementById('apply-filters-button'),
            // Элементы для отладки
            debugQueries: document.getElementById('debug-queries'),
            debugResponse: document.getElementById('debug-response')
        };
        
        // --- РЕНДЕРИНГ ЭЛЕМЕНТОВ ---

        function renderCard(item) {
            const priceFormatted = new Intl.NumberFormat('ru-RU', { 
                style: 'currency', 
                currency: 'RUB', 
                minimumFractionDigits: 0 
            }).format(item.price);

            // Обратите внимание: все кавычки в JS/HTML одинарные или двойные, 
            // чтобы не конфликтовать с ''' в Python
            return `
                <div class="equipment-card p-4 rounded-xl shadow-lg relative flex flex-col justify-between h-full">
                    ${item.rank === 1 ? 
                        `<div class="rank-badge absolute top-3 right-3 bg-yellow-500 text-gray-900 text-xs font-bold px-3 py-1 rounded-full shadow-xl flex items-center">
                            <i data-lucide="star" class="w-4 h-4 mr-1 fill-current"></i>Лучший Ранг
                        </div>` : ''}

                    <h3 class="text-xl font-semibold text-blue-300 mb-2">${item.title}</h3>
                    
                    <p class="text-sm text-gray-400 mb-3">${item.snippet}</p>

                    <div class="flex flex-col gap-2 mt-auto">
                        <p class="text-lg font-bold text-green-400">${priceFormatted}</p>
                        <p class="text-xs text-gray-500">Источник: ${item.source}</p>
                        <a href="${item.uri}" target="_blank" class="text-blue-400 hover:text-blue-300 transition duration-150 text-sm flex items-center">
                            Перейти к предложению <i data-lucide="external-link" class="w-4 h-4 ml-1"></i>
                        </a>
                    </div>
                </div>
            `;
        }
        
        function renderPagination() {
            elements.pagination.innerHTML = '';
            const totalPages = Math.ceil(filteredResults.length / RESULTS_PER_PAGE);

            if (totalPages <= 1) return;

            const createButton = (label, page, isActive = false, isDisabled = false) => {
                const button = document.createElement('button');
                button.textContent = label;
                button.className = `px-4 py-2 rounded-lg font-semibold transition duration-150 ${
                    isActive ? 'bg-blue-600 text-white' : 
                    isDisabled ? 'bg-gray-700 text-gray-500 cursor-not-allowed' :
                    'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`;
                button.disabled = isDisabled;
                if (!isDisabled) {
                    button.addEventListener('click', () => {
                        currentPage = page;
                        renderCurrentPage();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                }
                return button;
            };

            // Кнопка "Назад"
            elements.pagination.appendChild(createButton('Назад', currentPage - 1, false, currentPage === 1));

            // Кнопки страниц (отображаем все)
            for (let i = 1; i <= totalPages; i++) {
                elements.pagination.appendChild(createButton(i, i, i === currentPage));
            }

            // Кнопка "Вперед"
            elements.pagination.appendChild(createButton('Вперед', currentPage + 1, false, currentPage === totalPages));
        }

        function renderCurrentPage() {
            elements.grid.innerHTML = '';
            
            if (filteredResults.length === 0) {
                elements.grid.innerHTML = `
                    <div class="no-results col-span-full">
                        <p class="text-xl text-gray-400"><i data-lucide="alert-triangle" class="w-8 h-8 mr-2 inline-block"></i> К сожалению, по вашему запросу ничего не найдено.</p>
                    </div>
                `;
                lucide.createIcons();
                renderPagination();
                return;
            }

            const start = (currentPage - 1) * RESULTS_PER_PAGE;
            const end = start + RESULTS_PER_PAGE;
            const currentItems = filteredResults.slice(start, end);

            elements.grid.innerHTML = currentItems.map(renderCard).join('');
            lucide.createIcons();
            renderPagination();
        }

        // --- ЛОГИКА ФИЛЬТРАЦИИ И СОРТИРОВКИ ---

        function applyFilters() {
            currentPage = 1; // Сброс страницы при применении фильтров
            
            // 1. Фильтрация по цене
            const min = parseInt(elements.priceMin.value) || 0;
            const max = parseInt(elements.priceMax.value) || Infinity;

            let tempResults = allResults.filter(item => item.price >= min && item.price <= max);

            // 2. Сортировка
            const sortType = elements.sortBy.value;

            tempResults.sort((a, b) => {
                if (sortType === 'price_asc') {
                    return a.price - b.price; 
                } else if (sortType === 'price_desc') {
                    return b.price - a.price;
                } else if (sortType === 'rank_desc') {
                    return a.rank - b.rank; // Меньшее число ранга - лучше.
                }
                return 0;
            });

            filteredResults = tempResults;
            renderCurrentPage();
        }

        // --- СЕТЕВОЙ ЗАПРОС ---

        async function fetchSearchResults(queries) {
            const queryData = { queries: queries };
            let rawResponse = null;

            // Обновляем панель отладки
            elements.debugQueries.textContent = JSON.stringify(queries, null, 2);
            elements.debugResponse.textContent = "Отправка POST-запроса на " + API_URL + "...";

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(queryData)
                });
                
                rawResponse = await response.text();
                const data = JSON.parse(rawResponse);
                
                // Обновляем панель отладки с полным JSON-ответом
                elements.debugResponse.textContent = JSON.stringify(data, null, 2);

                if (!response.ok) {
                    throw new Error(`Ошибка HTTP-статуса ${response.status}. Проверьте бэкенд.`);
                }
                
                if (data.status === 'success' && Array.isArray(data.results)) {
                    elements.status.textContent = `Найдено ${data.results.length} предложений.`;
                    return data.results;
                } else {
                    throw new Error(data.message || 'Неверный формат ответа от API.');
                }

            } catch (error) {
                console.error("СЕТЕВАЯ/ПАРСИНГ ОШИБКА:", error);
                
                elements.status.textContent = `КРИТИЧЕСКАЯ ОШИБКА: Сервер недоступен или вернул некорректные данные. См. панель отладки.`;

                if (rawResponse) {
                    elements.debugResponse.textContent = `Ошибка: ${error.message}\n\nНеобработанный ответ:\n${rawResponse}`;
                } else {
                    elements.debugResponse.textContent = `Ошибка: ${error.message}\n\nСервер не ответил.`;
                }

                // Возвращаем пустой массив, заглушки удалены
                return []; 
            }
        }
        
        // --- ПЕРЕВОД И ОБРАБОТКА ЗАПРОСА ---

        async function translateQuery(query) {
            // Используем встроенный словарь для имитации перевода
            
            const translationMap = {
                'микрофон': 'microphone',
                'пульт': 'mixer',
                'колонки': 'speakers',
                'усилитель': 'amplifier',
                'наушники': 'headphones',
                'синтезатор': 'synthesizer',
                'dj контроллер': 'dj controller',
                'аудиоинтерфейс': 'audio interface',
                'свет': 'lighting',
                'световой': 'lighting',
                'кабель': 'cable',
                'стойка': 'stand',
                'чехол': 'case',
                'контроллер': 'controller',
                'проигрыватель': 'player'
            };

            const lowerQuery = query.toLowerCase();
            let englishQuery = lowerQuery;

            // Поиск ключевого слова для замены
            for (const ruWord in translationMap) {
                // Ищем слово с границами
                const regex = new RegExp(`\\b${ruWord}\\b`, 'g');
                if (regex.test(lowerQuery)) {
                    englishQuery = lowerQuery.replace(regex, translationMap[ruWord]);
                    break; 
                }
            }
            
            // Возвращаем массив запросов: [русский, английский]
            return [lowerQuery, englishQuery];
        }

        // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

        elements.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = elements.input.value.trim();
            if (!query) return;

            elements.button.disabled = true;
            elements.button.innerHTML = `<i data-lucide="loader" class="w-5 h-5 mr-2 animate-spin"></i> Поиск...`;
            elements.status.textContent = `Ищем предложения по запросу: "${query}"...`;

            try {
                const translatedQueries = await translateQuery(query); 
                const apiResults = await fetchSearchResults(translatedQueries); 

                allResults = apiResults;
                
                // Устанавливаем максимальную цену
                if (allResults.length > 0) {
                    const maxPrice = allResults.reduce((max, item) => Math.max(max, item.price), 0);
                    // Оставляем placeholder, но не трогаем value
                    elements.priceMax.placeholder = maxPrice;
                } else {
                    elements.priceMax.placeholder = '500000';
                }
                
                applyFilters();
                
            } catch (error) {
                console.error("Критическая ошибка в логике клиента:", error);
            } finally {
                elements.button.disabled = false;
                elements.button.innerHTML = `<i data-lucide="search" class="w-5 h-5 mr-2"></i> Искать`;
                lucide.createIcons();
            }
        });

        elements.applyFiltersButton.addEventListener('click', applyFilters);
        elements.sortBy.addEventListener('change', applyFilters);
        
        // Запускаем тестовый поиск при загрузке страницы
        window.addEventListener('load', () => {
            elements.input.value = "DJ контроллер";
            // Используем setTimeout, чтобы убедиться, что все listeners установлены
            setTimeout(() => {
                elements.form.dispatchEvent(new Event('submit'));
            }, 100);
        });

    </script>
</body>
</html>
''' # ЗАКРЫВАЕМ СТРОКУ ТРОЙНЫМИ ОДИНАРНЫМИ КАВЫЧКАМИ

# --- ФУНКЦИЯ ДЛЯ ИМИТАЦИИ ПАРСИНГА ЯНДЕКС (БЕЗ ИЗМЕНЕНИЙ) ---
def perform_yandex_search(query):
    """
    Имитирует выполнение поиска через Requests и BeautifulSoup.
    Возвращает структурированный Mock-массив,
    """
    print(f"Выполнение имитации запроса к внешнему источнику для: {query}")
    time.sleep(0.5) 
    
    # --- СЕКЦИЯ, КОТОРУЮ НЕОБХОДИМО ЗАМЕНИТЬ РЕАЛЬНОЙ ЛОГИКОЙ ПАРСИНГА ---
    
    mockData = []
    # Теперь генерируем 20 результатов (2.3.b)
    basePrice = random.randint(10000, 60000) 

    for i in range(20):
        # Генерируем данные с учетом реальных полей, ожидаемых фронтендом
        price = basePrice + (1000 * (i+1)) - (500 * (i % 2))
        # rank 1 должен быть только у одного элемента
        rank = 1 if i == 0 else random.randint(2, 6)
        
        mockData.append({
            "id": i + 1,
            "title": f"[{'EN' if i%2==0 else 'RU'} ИМИТАЦИЯ] {query} — Результат №{i + 1}",
            "snippet": f"Это краткое описание имитирует результат, полученный парсингом Яндекс. Мы нашли отличные цены на {query}. Ранг: {rank}.",
            "uri": f"https://mock-yandex.com/item/{i + 1}",
            "source": f"Яндекс.Маркет Имитация {chr(65 + i // 5)}", 
            "price": max(100, price), 
            "rank": rank 
        })
    
    # Сортируем по цене, как требует фронтенд (2.4.b)
    mockData.sort(key=lambda x: x['price'])
    return mockData

# --- МАРШРУТ API ---
@app.route('/api/search', methods=['GET', 'POST'])
def search_catalog():
    if request.method == 'GET':
        # Если это GET-запрос (пользователь открыл страницу в браузере),
        # отдаем полноценный HTML-интерфейс.
        response = make_response(HTML_CONTENT)
        response.headers["Content-Type"] = "text/html"
        return response

    # Если это POST-запрос (с фронтенда для получения данных), 
    # выполняем основную логику API.
    
    # 1. Обработка входящего JSON
    try:
        data = request.get_json()
    except Exception:
        # 400 Bad Request
        return jsonify({"error": "Не удалось распарсить JSON-тело запроса. Ожидается 'application/json'."}), 400

    # 2. Извлекаем массив 'queries'
    queries = data.get('queries')
    
    if not queries or not isinstance(queries, list) or not queries[0]:
        # 400 Bad Request
        return jsonify({
            "error": "Отсутствует или неверный параметр 'queries'. Ожидается массив строк: {'queries': ['русский', 'english']}"
        }), 400

    # 3. Используем первый запрос из массива для имитации поиска
    query_to_use = queries[0]
    
    # Вызываем функцию, имитирующую поиск (возвращает 20 результатов)
    results = perform_yandex_search(query_to_use)

    # 4. Возвращаем успешный ответ
    # 2.3.c) Структура ответа API
    return jsonify({
        "status": "success",
        "query_used": query_to_use,
        "results_count": len(results),
        "results": results 
    }), 200

# Для локального запуска
if __name__ == '__main__':
    # Внимание: для Render хост должен быть '0.0.0.0'
    # Используйте порт 5000 или тот, который требует Render
    app.run(host='0.0.0.0', port=5000)
