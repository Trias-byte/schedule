"""
Базовая конфигурация pytest для Schedule Manager тестов.
"""

import pytest
import datetime
from fastapi.testclient import TestClient
from schedule_manager.main import app
from schedule_manager.core import ScheduleManager


# ==========================================
# Базовые фикстуры
# ==========================================

@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def schedule_manager():
    """ScheduleManager instance for testing."""
    return ScheduleManager()


@pytest.fixture
def sample_data():
    """Простые тестовые данные."""
    return {
        "days": [
            {"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"},
            {"id": 2, "date": "2024-01-16", "start": "10:00", "end": "18:00"}
        ],
        "timeslots": [
            {"id": 1, "day_id": 1, "start": "09:00", "end": "10:30"},
            {"id": 2, "day_id": 1, "start": "14:00", "end": "15:30"},
            {"id": 3, "day_id": 2, "start": "11:00", "end": "12:00"}
        ]
    }


@pytest.fixture
def simple_day_data():
    """Простые данные дня."""
    return {"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}


@pytest.fixture
def simple_timeslot_data():
    """Простые данные временного слота."""
    return {"id": 1, "day_id": 1, "start": "10:00", "end": "11:00"}


@pytest.fixture
def populated_schedule_manager(sample_data):
    """ScheduleManager с загруженными тестовыми данными."""
    manager = ScheduleManager()
    manager.set_data(sample_data["days"], sample_data["timeslots"])
    return manager


@pytest.fixture
def empty_day_data():
    """Данные дня без временных слотов."""
    return {
        "days": [{"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}],
        "timeslots": []
    }


@pytest.fixture
def complex_schedule_data():
    """Сложные данные расписания с множественными слотами."""
    days = []
    timeslots = []
    
    # Создаем 5 дней
    for day_id in range(1, 6):
        days.append({
            "id": day_id,
            "date": f"2024-01-{14 + day_id:02d}",
            "start": "09:00",
            "end": "17:00"
        })
        
        # Добавляем 2-3 слота на каждый день
        for slot_num in range(2 if day_id % 2 == 0 else 3):
            timeslots.append({
                "id": day_id * 10 + slot_num,
                "day_id": day_id,
                "start": f"{10 + slot_num * 2:02d}:00",
                "end": f"{11 + slot_num * 2:02d}:00"
            })
    
    return {"days": days, "timeslots": timeslots}


@pytest.fixture
def overlapping_slots_data():
    """Данные с пересекающимися слотами."""
    return {
        "days": [{"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}],
        "timeslots": [
            {"id": 1, "day_id": 1, "start": "09:00", "end": "11:00"},
            {"id": 2, "day_id": 1, "start": "10:30", "end": "12:30"},
            {"id": 3, "day_id": 1, "start": "12:00", "end": "14:00"},
            {"id": 4, "day_id": 1, "start": "13:30", "end": "15:30"}
        ]
    }


# ==========================================
# Фикстуры для невалидных данных
# ==========================================

@pytest.fixture
def invalid_day_data():
    """Невалидные данные дня."""
    return [
        {"id": "not_int", "date": "2024-01-15", "start": "09:00", "end": "17:00"},
        {"id": 1, "date": "invalid-date", "start": "09:00", "end": "17:00"},
        {"id": 2, "date": "2024-01-15", "start": "invalid-time", "end": "17:00"},
        {"id": 3, "date": "2024-01-15", "start": "09:00", "end": "invalid-time"}
    ]


@pytest.fixture
def invalid_timeslot_data():
    """Невалидные данные временного слота."""
    return [
        {"id": "not_int", "day_id": 1, "start": "09:00", "end": "10:00"},
        {"id": 1, "day_id": "not_int", "start": "09:00", "end": "10:00"},
        {"id": 2, "day_id": 1, "start": "invalid-time", "end": "10:00"},
        {"id": 3, "day_id": 1, "start": "09:00", "end": "invalid-time"}
    ]


# ==========================================
# Фикстуры для тестирования API
# ==========================================

@pytest.fixture
def api_headers():
    """Стандартные заголовки для API запросов."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


@pytest.fixture
def malformed_json_data():
    """Некорректные JSON данные для тестирования."""
    return [
        '{"days": [}',  # Невалидный JSON
        '{"days": [], "timeslots": [}',  # Невалидный JSON
        '',  # Пустая строка
        'not json at all'  # Не JSON
    ]


# ==========================================
# Фикстуры для тестирования производительности
# ==========================================

@pytest.fixture
def large_dataset():
    """Большой набор данных для тестирования производительности."""
    days = []
    timeslots = []
    
    # Создаем 100 дней
    for day_id in range(1, 101):
        days.append({
            "id": day_id,
            "date": f"2024-{((day_id - 1) // 30) + 1:02d}-{((day_id - 1) % 30) + 1:02d}",
            "start": "09:00",
            "end": "17:00"
        })
        
        # 5-10 слотов на каждый день
        slots_count = 5 + (day_id % 6)
        for slot_num in range(slots_count):
            hour = 9 + slot_num
            if hour < 17:
                timeslots.append({
                    "id": day_id * 100 + slot_num,
                    "day_id": day_id,
                    "start": f"{hour:02d}:00",
                    "end": f"{hour:02d}:50"
                })
    
    return {"days": days, "timeslots": timeslots}


@pytest.fixture
def performance_schedule_manager(large_dataset):
    """ScheduleManager с большим набором данных."""
    manager = ScheduleManager()
    manager.set_data(large_dataset["days"], large_dataset["timeslots"])
    return manager


# ==========================================
# Фикстуры для реальных сценариев
# ==========================================

@pytest.fixture
def doctor_schedule_data():
    """Данные расписания врача."""
    return {
        "days": [
            {"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"},  # Понедельник
            {"id": 2, "date": "2024-01-16", "start": "09:00", "end": "17:00"},  # Вторник
            {"id": 3, "date": "2024-01-17", "start": "09:00", "end": "17:00"},  # Среда
            {"id": 4, "date": "2024-01-18", "start": "09:00", "end": "17:00"},  # Четверг
            {"id": 5, "date": "2024-01-19", "start": "09:00", "end": "17:00"},  # Пятница
        ],
        "timeslots": [
            # Понедельник - загруженный день
            {"id": 1, "day_id": 1, "start": "09:00", "end": "10:00"},
            {"id": 2, "day_id": 1, "start": "10:30", "end": "11:30"},
            {"id": 3, "day_id": 1, "start": "14:00", "end": "15:00"},
            {"id": 4, "day_id": 1, "start": "15:30", "end": "16:30"},
            
            # Среда - средняя загрузка
            {"id": 5, "day_id": 3, "start": "10:00", "end": "11:00"},
            {"id": 6, "day_id": 3, "start": "15:00", "end": "16:00"},
            
            # Пятница - один прием
            {"id": 7, "day_id": 5, "start": "14:00", "end": "15:00"},
            
            # Вторник и четверг - свободны
        ]
    }


@pytest.fixture
def conference_room_schedule_data():
    """Данные расписания конференц-зала."""
    return {
        "days": [
            {"id": 1, "date": "2024-01-15", "start": "08:00", "end": "18:00"},  # Понедельник
            {"id": 2, "date": "2024-01-16", "start": "08:00", "end": "18:00"},  # Вторник
            {"id": 3, "date": "2024-01-17", "start": "08:00", "end": "18:00"},  # Среда
            {"id": 4, "date": "2024-01-18", "start": "08:00", "end": "18:00"},  # Четверг
            {"id": 5, "date": "2024-01-19", "start": "08:00", "end": "18:00"},  # Пятница
        ],
        "timeslots": [
            # Понедельник - утренние встречи
            {"id": 1, "day_id": 1, "start": "09:00", "end": "10:30"},
            {"id": 2, "day_id": 1, "start": "11:00", "end": "12:00"},
            
            # Среда - весь день занят семинаром
            {"id": 3, "day_id": 3, "start": "08:30", "end": "17:30"},
            
            # Пятница - послеобеденная встреча
            {"id": 4, "day_id": 5, "start": "14:00", "end": "16:00"},
        ]
    }


# ==========================================
# Утилитарные функции
# ==========================================

def time_to_minutes(time_str: str) -> int:
    """Конвертирует время в минуты с начала дня."""
    hour, minute = map(int, time_str.split(":"))
    return hour * 60 + minute


def minutes_to_time(minutes: int) -> str:
    """Конвертирует минуты в строку времени."""
    hour, minute = divmod(minutes, 60)
    return f"{hour:02d}:{minute:02d}"


def validate_no_overlaps(intervals: list) -> bool:
    """Проверяет, что интервалы не пересекаются."""
    for i, (start1, end1) in enumerate(intervals):
        start1_min = time_to_minutes(start1)
        end1_min = time_to_minutes(end1)
        
        for j, (start2, end2) in enumerate(intervals[i+1:], i+1):
            start2_min = time_to_minutes(start2)
            end2_min = time_to_minutes(end2)
            
            # Интервалы пересекаются если не выполняется условие:
            # end1 <= start2 OR end2 <= start1
            if not (end1_min <= start2_min or end2_min <= start1_min):
                return False
    return True


# ==========================================
# Pytest конфигурация
# ==========================================

def pytest_configure(config):
    """Конфигурация pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Автоматически добавляет маркеры к тестам."""
    for item in items:
        # Добавляем unit маркер если нет других специфичных маркеров
        if not any(mark.name in ["integration", "performance"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# ==========================================
# Cleanup фикстуры
# ==========================================

@pytest.fixture(autouse=True)
def cleanup():
    """Автоматическая очистка после каждого теста."""
    yield
    # Здесь можно добавить очистку если необходимо
    pass