# Schedule Manager

Высокопроизводительная система управления расписанием с оптимизацией на основе Interval Tree (красно-черные деревья). Предназначена для быстрого поиска свободного времени, проверки доступности и управления временными слотами.

## 🚀 Основные возможности

- **Быстрый поиск свободного времени** - O(log n) сложность поиска
- **Проверка доступности временных слотов** - мгновенная проверка пересечений
- **Оптимизированная структура данных** - Interval Tree на основе красно-черных деревьев
- **RESTful API** - полнофункциональный API с документацией
- **Контейнеризация** - готовые Docker конфигурации для разработки и продакшена
- **Комплексное тестирование** - юнит и интеграционные тесты с высоким покрытием

## 📋 Содержание

- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Использование](#-использование)
- [API Документация](#-api-документация)
- [Тестирование](#-тестирование)
- [Разработка](#-разработка)
- [Docker](#-docker)
- [Производительность](#-производительность)
- [Архитектура](#-архитектура)

## 🎯 Быстрый старт

### Локальный запуск

```bash
# Клонируйте репозиторий
git clone https://github.com/Trias-byte/schedule
cd schedule

# Установите зависимости
pip install -e .

# Запустите сервер
uvicorn schedule_manager.main:app --reload

# Откройте браузер
open http://localhost:8000/docs
```

### Docker запуск

```bash
# Запуск в режиме разработки
docker-compose --profile development up

# Запуск в production режиме
docker-compose up
```

## 📦 Установка

### Требования

- Python 3.8+
- pip или uv (рекомендуется)

### Установка зависимостей

#### Использование uv (рекомендуется)

```bash

pip install uv

# Создание виртуального окружения и установка зависимостей
uv venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows

# Установка в режиме разработки
uv pip install -e ".[dev,test]"
```

#### Использование pip

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -e ".[dev,test]"
```

### Переменные окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
cp .env.example .env
```

Основные параметры:
- `HOST` - хост сервера (по умолчанию: 0.0.0.0)
- `PORT` - порт сервера (по умолчанию: 8000)
- `LOG_LEVEL` - уровень логирования (info, debug, warning, error)
- `ENDPOINT_URL` - URL внешнего API для загрузки данных

## 🔧 Использование

### Программный интерфейс

```python
from schedule_manager import ScheduleManager

# Создание менеджера
manager = ScheduleManager()

# Загрузка данных из внешнего API
manager.load_data()

# Или установка данных напрямую
manager.set_data(days_data, timeslots_data)

# Получение занятых интервалов
busy_intervals = manager.get_busy_intervals("2024-01-15")
print(busy_intervals)  # [("09:00", "10:30"), ("14:00", "15:30")]

# Получение свободного времени
free_time = manager.get_free_time("2024-01-15")
print(free_time)  # [("10:30", "14:00"), ("15:30", "17:00")]

# Проверка доступности
is_available = manager.is_time_available("2024-01-15", "12:00", "13:00")
print(is_available)  # True

# Поиск свободного слота
free_slot = manager.find_free_slot("2024-01-15", 60)  # 60 минут
print(free_slot)  # "10:30"
```

### Запуск сервера

```bash
# Режим разработки с hot-reload
uvicorn schedule_manager.main:app --reload --host 0.0.0.0 --port 8000

# Продакшен режим
python -m schedule_manager.main

# Или через entry point
schedule-manager
```

## 📖 API Документация

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/docs` | Swagger UI документация |
| `GET` | `/health` | Проверка состояния сервиса |
| `POST` | `/api/v1/data` | Загрузка данных |
| `POST` | `/api/v1/reload` | Перезагрузка данных из внешнего API |
| `GET` | `/api/v1/busy/{date}` | Получение занятых интервалов |
| `GET` | `/api/v1/free/{date}` | Получение свободного времени |
| `GET` | `/api/v1/available/{date}` | Проверка доступности времени |
| `GET` | `/api/v1/find-slot/{date}` | Поиск свободного слота |
| `GET` | `/api/v1/stats` | Статистика производительности |

### Примеры использования

#### Загрузка данных

```bash
curl -X POST "http://localhost:8000/api/v1/data" \
  -H "Content-Type: application/json" \
  -d '{
    "days": [
      {"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}
    ],
    "timeslots": [
      {"id": 1, "day_id": 1, "start": "10:00", "end": "11:00"}
    ]
  }'
```

#### Получение занятых интервалов

```bash
curl "http://localhost:8000/api/v1/busy/2024-01-15"
```

#### Проверка доступности времени

```bash
curl "http://localhost:8000/api/v1/available/2024-01-15?start_time=12:00&end_time=13:00"
```

#### Поиск свободного слота

```bash
curl "http://localhost:8000/api/v1/find-slot/2024-01-15?duration_minutes=60"
```

## 🧪 Тестирование

### Запуск всех тестов

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=schedule_manager --cov-report=html

# Запуск с подробным выводом
pytest -v
```

### Запуск конкретных тестов

```bash
# Только юнит тесты
pytest tests/unit/

# Только интеграционные тесты
pytest tests/integration/

# Тесты по маркерам
pytest -m "not slow"
pytest -m "unit"
pytest -m "integration"
pytest -m "performance"
```

### Запуск тестов с фильтрацией

```bash
# Конкретный тест
pytest tests/unit/test_core.py::TestScheduleManager::test_get_busy_intervals

# Тесты по паттерну
pytest -k "test_busy"

# Исключение медленных тестов
pytest -m "not slow"
```


### Генерация отчетов

```bash
# HTML отчет покрытия
pytest --cov=schedule_manager --cov-report=html
open htmlcov/index.html

# XML отчет для CI
pytest --cov=schedule_manager --cov-report=xml

# Отчет в терминал
pytest --cov=schedule_manager --cov-report=term-missing
```

### Структура тестов

```
tests/
├── conftest.py              # Общие фикстуры
├── unit/                    # Юнит тесты
│   ├── test_core.py        # Тесты основной логики
│   └── test_interval_tree.py # Тесты структуры данных
└── integration/             # Интеграционные тесты
    ├── test_api.py         # Тесты API
    └── test_workflow.py    # Тесты сценариев

```

### Настройка тестирования

Конфигурация в `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short --cov=schedule_manager --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

## ⚡ Производительность

### Оптимизации

- **Interval Tree** - O(log n) поиск пересечений
- **Красно-черные деревья** - самобалансирующиеся деревья
- **Индексация по датам** - быстрый доступ к данным дня
- **Lazy loading** - данные загружаются по требованию

### Benchmark результаты

```
Операция             | Время (ms) | Сложность
---------------------|------------|----------
Поиск пересечений    | 0.1        | O(log n)
Вставка слота        | 0.05       | O(log n)
Получение свободного | 0.2        | O(k)
```

### Мониторинг

```bash
# Получение статистики
curl http://localhost:8000/api/v1/stats

# Проверка health
curl http://localhost:8000/health
```

## 🏗️ Архитектура

### Структура проекта

```
schedule_manager/
├── __init__.py          # Основные экспорты
├── core.py             # Основная логика и IntervalTree
├── main.py             # FastAPI приложение
└── benchmark.py        # Инструменты производительности
```

### Основные компоненты

#### ScheduleManager
Главный класс для управления расписанием:
- Загрузка и валидация данных
- Построение индексов
- Поиск свободного времени

#### IntervalTree
Оптимизированная структура данных:
- Красно-черное дерево
- Поиск пересечений за O(log n)
- Автоматическое балансирование

#### API Layer
FastAPI приложение с:
- Асинхронной обработкой
- Валидацией данных
- Обработкой ошибок
- Документацией

### Алгоритмы

1. **Поиск пересечений**: Использует augmented interval tree
2. **Поиск свободного времени**: Проход по отсортированным интервалам
3. **Вставка**: Поддержание свойств красно-черного дерева
4. **Балансировка**: Автоматические повороты при вставке


## 👥 Авторы

- **TriasByte** - [triasfreelance@gmail.com](mailto:triasfreelance@gmail.com)