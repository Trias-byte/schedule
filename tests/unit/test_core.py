"""
Исправленные unit тесты для core.py
"""

import pytest
import datetime
from schedule_manager.core import ScheduleManager, Day, TimeSlot, IntervalTree


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
def schedule_manager():
    """ScheduleManager instance for testing."""
    return ScheduleManager()


class TestScheduleManager:
    """Тесты ScheduleManager."""
    
    def test_set_data(self, schedule_manager, sample_data):
        """Тест установки данных."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        assert len(schedule_manager.days) == 2
        assert len(schedule_manager.timeslots) == 3
        assert len(schedule_manager.interval_trees) == 2
    
    def test_get_busy_intervals(self, schedule_manager, sample_data):
        """Тест получения занятых интервалов."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        intervals = schedule_manager.get_busy_intervals("2024-01-15")
        expected = [("09:00", "10:30"), ("14:00", "15:30")]
        assert intervals == expected
    
    def test_get_free_time(self, schedule_manager, sample_data):
        """Тест получения свободного времени."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        free_time = schedule_manager.get_free_time("2024-01-15")
        expected = [("10:30", "14:00"), ("15:30", "17:00")]
        assert free_time == expected
    
    def test_is_time_available(self, schedule_manager, sample_data):
        """Тест проверки доступности времени."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        # Свободное время
        assert schedule_manager.is_time_available("2024-01-15", "12:00", "13:00") is True
        
        # Занятое время
        assert schedule_manager.is_time_available("2024-01-15", "09:30", "10:00") is False
    
    def test_find_free_slot(self, schedule_manager, sample_data):
        """Тест поиска свободного слота."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        # Ищем 60-минутный слот
        result = schedule_manager.find_free_slot("2024-01-15", 60)
        assert result == "10:30"
        
        # Ищем слишком большой слот
        result = schedule_manager.find_free_slot("2024-01-15", 300)
        assert result is None
    
    def test_empty_day(self, schedule_manager):
        """Тест с пустым днем (без слотов)."""
        days = [{"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}]
        timeslots = []
        
        schedule_manager.set_data(days, timeslots)
        
        # Должен вернуть пустой список занятых интервалов
        busy = schedule_manager.get_busy_intervals("2024-01-15")
        assert busy == []
        
        # Должен вернуть весь день как свободный
        free = schedule_manager.get_free_time("2024-01-15")
        assert free == [("09:00", "17:00")]
        
        # Любое время в рабочих часах должно быть доступно
        assert schedule_manager.is_time_available("2024-01-15", "12:00", "13:00") is True
    
    def test_invalid_date(self, schedule_manager, sample_data):
        """Тест с неверной датой."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        # Несуществующая дата
        with pytest.raises(RuntimeError, match="не найден"):
            schedule_manager.get_busy_intervals("2024-12-25")
        
        # Неверный формат даты
        with pytest.raises(ValueError, match="Неверный формат даты"):
            schedule_manager.get_busy_intervals("invalid-date")
    
    def test_invalid_time_format(self, schedule_manager, sample_data):
        """Тест с неверным форматом времени."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        with pytest.raises(ValueError, match="Неверный формат времени"):
            schedule_manager.is_time_available("2024-01-15", "invalid-time", "13:00")
    
    def test_invalid_time_range(self, schedule_manager, sample_data):
        """Тест с неверным диапазоном времени."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        with pytest.raises(ValueError, match="должно быть меньше"):
            schedule_manager.is_time_available("2024-01-15", "15:00", "12:00")
    
    def test_time_outside_working_hours(self, schedule_manager, sample_data):
        """Тест времени вне рабочих часов."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        # До рабочих часов
        assert schedule_manager.is_time_available("2024-01-15", "08:00", "09:00") is False
        
        # После рабочих часов
        assert schedule_manager.is_time_available("2024-01-15", "17:00", "18:00") is False
    
    def test_no_data_loaded(self, schedule_manager):
        """Тест без загруженных данных."""
        with pytest.raises(RuntimeError, match="Данные не загружены"):
            schedule_manager.get_busy_intervals("2024-01-15")
    
    def test_invalid_duration(self, schedule_manager, sample_data):
        """Тест с неверной продолжительностью."""
        schedule_manager.set_data(sample_data["days"], sample_data["timeslots"])
        
        with pytest.raises(ValueError, match="должна быть положительной"):
            schedule_manager.find_free_slot("2024-01-15", -10)
        
        with pytest.raises(ValueError, match="должна быть положительной"):
            schedule_manager.find_free_slot("2024-01-15", 0)


class TestDay:
    """Тесты класса Day."""
    
    def test_create_from_dict(self):
        """Тест создания Day из словаря."""
        data = {"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}
        day = Day.from_dict(data)
        
        assert day.id == 1
        assert day.date == datetime.date(2024, 1, 15)
        assert day.start == datetime.time(9, 0)
        assert day.end == datetime.time(17, 0)
    
    def test_to_dict(self):
        """Тест преобразования Day в словарь."""
        day = Day(1, datetime.date(2024, 1, 15), datetime.time(9, 0), datetime.time(17, 0))
        result = day.to_dict()
        
        expected = {"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}
        assert result == expected
    
    def test_is_working_time(self):
        """Тест проверки рабочего времени."""
        day = Day(1, datetime.date(2024, 1, 15), datetime.time(9, 0), datetime.time(17, 0))
        
        # Рабочее время
        assert day.is_working_time(datetime.time(9, 0)) is True
        assert day.is_working_time(datetime.time(12, 0)) is True
        assert day.is_working_time(datetime.time(17, 0)) is True
        
        # Нерабочее время
        assert day.is_working_time(datetime.time(8, 59)) is False
        assert day.is_working_time(datetime.time(17, 1)) is False
    
    def test_invalid_date_format(self):
        """Тест с неверным форматом даты."""
        data = {"id": 1, "date": "invalid-date", "start": "09:00", "end": "17:00"}
        
        with pytest.raises(ValueError):
            Day.from_dict(data)
    
    def test_invalid_time_format(self):
        """Тест с неверным форматом времени."""
        data = {"id": 1, "date": "2024-01-15", "start": "invalid-time", "end": "17:00"}
        
        with pytest.raises(ValueError):
            Day.from_dict(data)


class TestTimeSlot:
    """Тесты класса TimeSlot."""
    
    def test_create_from_dict(self):
        """Тест создания TimeSlot из словаря."""
        data = {"id": 1, "day_id": 1, "start": "09:00", "end": "10:30"}
        slot = TimeSlot.from_dict(data)
        
        assert slot.id == 1
        assert slot.day_id == 1
        assert slot.start == datetime.time(9, 0)
        assert slot.end == datetime.time(10, 30)
    
    def test_to_dict(self):
        """Тест преобразования TimeSlot в словарь."""
        slot = TimeSlot(1, 1, datetime.time(9, 0), datetime.time(10, 30))
        result = slot.to_dict()
        
        expected = {"id": 1, "day_id": 1, "start": "09:00", "end": "10:30"}
        assert result == expected
    
    def test_duration_minutes(self):
        """Тест вычисления продолжительности."""
        slot = TimeSlot(1, 1, datetime.time(9, 0), datetime.time(10, 30))
        assert slot.duration_minutes() == 90
        
        # Нулевая продолжительность
        slot = TimeSlot(1, 1, datetime.time(9, 0), datetime.time(9, 0))
        assert slot.duration_minutes() == 0
    
    def test_overlaps_with(self):
        """Тест проверки пересечения слотов."""
        slot1 = TimeSlot(1, 1, datetime.time(9, 0), datetime.time(11, 0))
        slot2 = TimeSlot(2, 1, datetime.time(10, 0), datetime.time(12, 0))
        slot3 = TimeSlot(3, 1, datetime.time(11, 0), datetime.time(13, 0))
        
        # Пересекающиеся слоты
        assert slot1.overlaps_with(slot2) is True
        assert slot2.overlaps_with(slot1) is True
        
        # Соседние слоты (не пересекаются)
        assert slot1.overlaps_with(slot3) is False
        assert slot3.overlaps_with(slot1) is False
    
    def test_invalid_format(self):
        """Тест с неверным форматом данных."""
        data = {"id": 1, "day_id": 1, "start": "invalid-time", "end": "10:30"}
        
        with pytest.raises(ValueError):
            TimeSlot.from_dict(data)


class TestIntervalTree:
    """Базовые тесты IntervalTree."""
    
    def test_empty_tree(self):
        """Тест пустого дерева."""
        tree = IntervalTree()
        assert tree.is_empty() is True
        assert tree.size == 0
        assert tree.find_overlapping(10, 20) == []
        assert tree.get_all_intervals() == []
    
    def test_single_insert(self):
        """Тест вставки одного элемента."""
        tree = IntervalTree()
        tree.insert(10, 20, 1)
        
        assert tree.size == 1
        assert tree.is_empty() is False
        assert tree.get_all_intervals() == [(10, 20, 1)]
        assert tree.find_overlapping(15, 25) == [1]
    
    def test_insert_and_search(self):
        """Тест вставки и поиска."""
        tree = IntervalTree()
        tree.insert(10, 20, 1)
        tree.insert(15, 25, 2)
        tree.insert(30, 40, 3)
        
        assert tree.size == 3
        
        # Пересекающиеся интервалы
        overlapping = tree.find_overlapping(12, 18)
        assert set(overlapping) == {1, 2}
        
        # Не пересекающиеся интервалы
        overlapping = tree.find_overlapping(26, 28)
        assert overlapping == []
        
        # Интервал, пересекающийся с одним
        overlapping = tree.find_overlapping(35, 45)
        assert overlapping == [3]
    
    def test_multiple_inserts(self):
        """Тест множественных вставок."""
        tree = IntervalTree()
        intervals = [
            (0, 10, 1),
            (5, 15, 2),
            (10, 20, 3),
            (15, 25, 4),
            (30, 40, 5)
        ]
        
        for start, end, slot_id in intervals:
            tree.insert(start, end, slot_id)
        
        assert tree.size == 5
        
        # Получаем все интервалы (должны быть отсортированы по start)
        all_intervals = tree.get_all_intervals()
        expected = [(0, 10, 1), (5, 15, 2), (10, 20, 3), (15, 25, 4), (30, 40, 5)]
        assert all_intervals == expected
        
        # Тестируем различные пересечения
        assert set(tree.find_overlapping(7, 12)) == {1, 2, 3}
        assert set(tree.find_overlapping(18, 22)) == {3,4}
        assert tree.find_overlapping(26, 28) == []
    
    def test_exact_boundaries(self):
        """Тест точных границ интервалов."""
        tree = IntervalTree()
        tree.insert(10, 20, 1)
        tree.insert(20, 30, 2)
        
        # Точные границы не должны пересекаться
        assert tree.find_overlapping(10, 20) == [1]
        assert tree.find_overlapping(20, 30) == [2]
        
        # Пересекающийся интервал
        assert set(tree.find_overlapping(15, 25)) == {1, 2}
    
    def test_identical_intervals(self):
        """Тест идентичных интервалов с разными ID."""
        tree = IntervalTree()
        tree.insert(10, 20, 1)
        tree.insert(10, 20, 2)
        tree.insert(10, 20, 3)
        
        assert tree.size == 3
        overlapping = tree.find_overlapping(10, 20)
        assert set(overlapping) == {1, 2, 3}
    
    def test_zero_length_intervals(self):
        """Тест интервалов нулевой длины."""
        tree = IntervalTree()
        tree.insert(10, 10, 1)  # Нулевая длина
        tree.insert(15, 25, 2)
        
        assert tree.size == 2
        
        # Интервал нулевой длины не должен пересекаться с другими
        assert tree.find_overlapping(5, 15) == [1]
        assert tree.find_overlapping(20, 30) == [2]
    
    def test_large_numbers(self):
        """Тест с большими числами."""
        tree = IntervalTree()
        tree.insert(1000000, 2000000, 1)
        tree.insert(1500000, 2500000, 2)
        
        assert tree.size == 2
        overlapping = tree.find_overlapping(1750000, 1850000)
        assert set(overlapping) == {1, 2}
    
    def test_performance_many_intervals(self):
        """Базовый тест производительности с множеством интервалов."""
        tree = IntervalTree()
        
        # Вставляем много интервалов
        for i in range(100):
            tree.insert(i * 10, i * 10 + 5, i)
        
        assert tree.size == 100
        
        # Поиск должен работать быстро
        overlapping = tree.find_overlapping(500, 505)
        assert len(overlapping) == 1
        assert 50 in overlapping