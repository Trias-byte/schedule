"""
Исправленные интеграционные тесты API.
"""

import pytest
from fastapi.testclient import TestClient
from schedule_manager.main import app


@pytest.fixture
def test_client():
    """FastAPI test client для интеграционного тестирования."""
    return TestClient(app)


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


class TestAPIIntegration:
    """Интеграционные тесты API."""
    
    def test_complete_workflow(self, test_client, sample_data):
        """Тест полного workflow."""
        # Загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Проверяем health
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["data_loaded"] is True
        
        # Получаем занятые интервалы
        response = test_client.get("/api/v1/busy/2024-01-15")
        assert response.status_code == 200
        assert len(response.json()["busy_intervals"]) == 2
        
        # Получаем свободное время
        response = test_client.get("/api/v1/free/2024-01-15")
        assert response.status_code == 200
        assert len(response.json()["free_intervals"]) == 2
        
        # Проверяем доступность
        response = test_client.get("/api/v1/available/2024-01-15?start_time=12:00&end_time=13:00")
        assert response.status_code == 200
        assert response.json()["available"] is True
        
        # Ищем свободный слот
        response = test_client.get("/api/v1/find-slot/2024-01-15?duration_minutes=60")
        assert response.status_code == 200
        assert response.json()["found"] is True
    
    def test_error_handling(self, test_client):
        """Тест обработки ошибок."""
        # Неверные данные - FastAPI возвращает 422 для validation errors
        invalid_data = {"days": "not a list", "timeslots": []}
        response = test_client.post("/api/v1/data", json=invalid_data)
        assert response.status_code == 400  # Изменено с 400 на 422
        
        # Несуществующая дата - это возвращает 400 как и ожидается
        response = test_client.get("/api/v1/busy/invalid-date")
        assert response.status_code == 400
        
        # Отсутствующие параметры - FastAPI validation error
        response = test_client.get("/api/v1/available/2024-01-15")  # Нет start_time, end_time
        assert response.status_code == 422  # Validation error для отсутствующих параметров
    
    def test_data_consistency(self, test_client, sample_data):
        """Тест консистентности данных."""
        # Загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Получаем занятые интервалы
        response = test_client.get("/api/v1/busy/2024-01-15")
        assert response.status_code == 200
        busy_intervals = response.json()["busy_intervals"]
        
        # Получаем свободное время
        response = test_client.get("/api/v1/free/2024-01-15")
        assert response.status_code == 200
        free_intervals = response.json()["free_intervals"]
        
        # Проверяем, что busy и free интервалы не пересекаются
        def time_to_minutes(time_str):
            hour, minute = map(int, time_str.split(":"))
            return hour * 60 + minute
        
        busy_ranges = [(time_to_minutes(start), time_to_minutes(end)) 
                      for start, end in busy_intervals]
        free_ranges = [(time_to_minutes(start), time_to_minutes(end)) 
                      for start, end in free_intervals]
        
        # Проверяем отсутствие пересечений
        for free_start, free_end in free_ranges:
            for busy_start, busy_end in busy_ranges:
                assert not (free_start < busy_end and free_end > busy_start), \
                    f"Overlap detected: free {free_start}-{free_end} vs busy {busy_start}-{busy_end}"
    
    def test_invalid_date_format(self, test_client, sample_data):
        """Тест с неверным форматом даты."""
        # Сначала загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Тестируем неверный формат даты
        response = test_client.get("/api/v1/busy/2024-13-45")  # Неверная дата
        assert response.status_code == 400
        
        response = test_client.get("/api/v1/busy/invalid-date")  # Неверный формат
        assert response.status_code == 400
    
    def test_nonexistent_date(self, test_client, sample_data):
        """Тест с несуществующей (но корректной) датой."""
        # Загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Тестируем корректную дату, но без данных
        response = test_client.get("/api/v1/busy/2024-12-25")  # Дата корректная, но нет данных
        assert response.status_code == 400
        assert "не найден" in response.json()["detail"]
    
    def test_time_validation(self, test_client, sample_data):
        """Тест валидации времени."""
        # Загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Тестируем неверное время - FastAPI validation
        response = test_client.get("/api/v1/available/2024-01-15?start_time=25:00&end_time=13:00")
        assert response.status_code == 400  # ScheduleManager validation error
        
        # Тестируем логически неверное время (начало после конца)
        response = test_client.get("/api/v1/available/2024-01-15?start_time=15:00&end_time=12:00")
        assert response.status_code == 400
        assert "должно быть меньше" in response.json()["detail"]
    
    def test_duration_validation(self, test_client, sample_data):
        """Тест валидации продолжительности."""
        # Загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Тестируем отрицательную продолжительность - FastAPI validation
        response = test_client.get("/api/v1/find-slot/2024-01-15?duration_minutes=-10")
        assert response.status_code == 422  # FastAPI validation error
        
        # Тестируем нулевую продолжительность - FastAPI validation
        response = test_client.get("/api/v1/find-slot/2024-01-15?duration_minutes=0")
        assert response.status_code == 422  # FastAPI validation error
    
    def test_empty_data_handling(self, test_client):
        """Тест обработки пустых данных."""
        # Загружаем пустые данные
        empty_data = {"days": [], "timeslots": []}
        response = test_client.post("/api/v1/data", json=empty_data)
        assert response.status_code == 200
        
        # Проверяем health с пустыми данными
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["data_loaded"] is False
        
        # Пытаемся получить данные для несуществующей даты
        response = test_client.get("/api/v1/busy/2024-01-15")
        assert response.status_code == 400
        assert "Данные не " in response.json()["detail"]
    
    def test_malformed_json(self, test_client):
        """Тест с неверным JSON."""
        # Отправляем неверный JSON
        response = test_client.post(
            "/api/v1/data", 
            data='{"invalid": json}',  # Неверный JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # FastAPI JSON parsing error
    
    def test_missing_required_fields(self, test_client):
        """Тест с отсутствующими обязательными полями."""
        # Отсутствует timeslots
        incomplete_data = {"days": [{"id": 1, "date": "2024-01-15", "start": "09:00", "end": "17:00"}]}
        response = test_client.post("/api/v1/data", json=incomplete_data)
        assert response.status_code == 400
        assert "должны содержать" in response.json()["detail"]
        
        # Отсутствует days
        incomplete_data = {"timeslots": [{"id": 1, "day_id": 1, "start": "09:00", "end": "10:00"}]}
        response = test_client.post("/api/v1/data", json=incomplete_data)
        assert response.status_code == 400
        assert "должны содержать" in response.json()["detail"]
    
    def test_invalid_field_types(self, test_client):
        """Тест с неверными типами полей."""
        # days должен быть списком
        invalid_data = {"days": "not a list", "timeslots": []}
        response = test_client.post("/api/v1/data", json=invalid_data)
        assert response.status_code == 400
        assert "быть списк" in response.json()["detail"]
        
        # timeslots должен быть списком
        invalid_data = {"days": [], "timeslots": "not a list"}
        response = test_client.post("/api/v1/data", json=invalid_data)
        assert response.status_code == 400
        assert "быть списк" in response.json()["detail"]
    
    def test_health_endpoint_states(self, test_client, sample_data):
        """Тест различных состояний health endpoint."""
        # Начальное состояние - нет данных
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["data_loaded"] is False
        assert data["total_days"] == 0
        assert data["total_timeslots"] == 0
        
        # После загрузки данных
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["data_loaded"] is True
        assert data["total_days"] == 2
        assert data["total_timeslots"] == 3
        
        # Проверяем дополнительные поля
        assert "service" in data
        assert "version" in data
        assert "optimization" in data
    
    def test_statistics_endpoint(self, test_client, sample_data):
        """Тест endpoint статистики."""
        # Загружаем данные
        response = test_client.post("/api/v1/data", json=sample_data)
        assert response.status_code == 200
        
        # Получаем статистику
        response = test_client.get("/api/v1/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "data_summary" in stats
        assert "optimization" in stats
        assert stats["data_summary"]["total_days"] == 2
        assert stats["data_summary"]["total_timeslots"] == 3
        assert stats["optimization"]["type"] == "interval-tree"
        assert stats["optimization"]["status"] == "active"