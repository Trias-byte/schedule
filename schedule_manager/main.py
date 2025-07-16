import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
import uvicorn

from .core import ScheduleManager

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log") if os.path.exists("logs") else logging.NullHandler(),
    ]
)

logger = logging.getLogger(__name__)

schedule_manager = ScheduleManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Schedule Manager")
    os.makedirs("logs", exist_ok=True)
    
    try:
        await asyncio.get_event_loop().run_in_executor(None, schedule_manager.load_data)
        logger.info("✅ Данные успешно загружены при запуске")
        if hasattr(schedule_manager, 'get_statistics'):
            stats = schedule_manager.get_statistics()
            if stats:
                logger.info(f"📊 Загружено: {stats.get('total_days', 0)} дней, {stats.get('total_timeslots', 0)} слотов")
            
    except Exception as e:
        logger.warning(f"⚠️ Не удалось загрузить данные при запуске: {e}")
        logger.info("📝 Данные можно будет загрузить позже через API")
    
    yield
    logger.info("🔄 Завершение работы Schedule Manager")


app = FastAPI(
    title="Schedule Manager API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "TriasByte",
        "email": "triasfreelance@gmail.com",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ==========================================
# Обработчики ошибок
# ==========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработка ошибок валидации FastAPI (возвращает 422)."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({
            "detail": exc.errors(),
            "type": "validation_error",
            "message": "Данные не соответствуют ожидаемому формату"
        })
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Обработка RuntimeError (возвращает 500)."""
    logger.error(f"Runtime error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Внутренняя ошибка: {str(exc)}", "type": "runtime_error"}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Обработка ValueError (возвращает 400)."""
    logger.warning(f"Value error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработка HTTPException."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "http_error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка всех остальных исключений."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера", "type": "internal_error"}
    )


@app.get("/", include_in_schema=False)
async def root():
    """Перенаправление на документацию."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    try:
        health_data = {
            "status": "healthy",
            "service": "schedule-manager",
            "version": "1.0.0",
            "optimization": "interval-tree",
            "data_loaded": len(schedule_manager.days) > 0,
            "total_days": len(schedule_manager.days),
            "total_timeslots": len(schedule_manager.timeslots)
        }

        if hasattr(schedule_manager, 'get_statistics'):
            stats = schedule_manager.get_statistics()
            if stats:
                health_data.update({
                    "indexed_dates": stats.get("indexed_dates", 0),
                    "trees_count": len(schedule_manager.interval_trees),
                    "performance_optimization": "interval-tree-active"
                })
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "schedule-manager", 
                "error": str(e)
            }
        )


@app.get("/api/v1/data")
async def get_data():
    """
    Получить все данные расписания.
    
    Возвращает полную информацию о рабочих днях и временных слотах.
    """
    try:
        if not schedule_manager.days:
            raise HTTPException(
                status_code=404, 
                detail="Данные не загружены. Используйте POST /api/v1/reload для загрузки данных"
            )
        
        return {
            "days": [day.to_dict() for day in schedule_manager.days],
            "timeslots": [slot.to_dict() for slot in schedule_manager.timeslots],
            "summary": {
                "total_days": len(schedule_manager.days),
                "total_timeslots": len(schedule_manager.timeslots),
                "date_range": {
                    "start": min(day.date.strftime('%Y-%m-%d') for day in schedule_manager.days) if schedule_manager.days else None,
                    "end": max(day.date.strftime('%Y-%m-%d') for day in schedule_manager.days) if schedule_manager.days else None
                },
                "optimization_active": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@app.post("/api/v1/reload")
async def reload_data():
    """
    Перезагрузить данные с внешнего источника.
    
    Загружает свежие данные и перестраивает индексы.
    """
    try:
        await asyncio.get_event_loop().run_in_executor(None, schedule_manager.load_data)
        
        logger.info("✅ Данные успешно перезагружены")
        
        response_data = {
            "message": "Данные успешно перезагружены",
            "timestamp": "2024-10-10T12:00:00Z",  # В реальном приложении использовать datetime.utcnow()
            "summary": {
                "total_days": len(schedule_manager.days),
                "total_timeslots": len(schedule_manager.timeslots),
                "indexed_dates": len(schedule_manager.interval_trees)
            }
        }
        
        if hasattr(schedule_manager, 'get_statistics'):
            stats = schedule_manager.get_statistics()
            if stats:
                response_data["performance"] = {
                    "trees_built": len(schedule_manager.interval_trees),
                    "optimization_status": "active"
                }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных: {str(e)}")


@app.post("/api/v1/data")
async def set_data(data: Dict[str, Any]):
    """
    Установить данные напрямую.
    
    Принимает данные в JSON формате и перестраивает все индексы.
    """
    try:
        # Проверяем наличие обязательных ключей
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400,
                detail="Данные должны быть объектом JSON"
            )
        
        if 'days' not in data:
            raise HTTPException(
                status_code=400,
                detail="Данные должны содержать ключ 'days'"
            )
        
        if 'timeslots' not in data:
            raise HTTPException(
                status_code=400,
                detail="Данные должны содержать ключ 'timeslots'"
            )
        
        # Проверяем типы данных
        if not isinstance(data['days'], list):
            raise HTTPException(
                status_code=400,
                detail="'days' должен быть списком"
            )
        
        if not isinstance(data['timeslots'], list):
            raise HTTPException(
                status_code=400,
                detail="'timeslots' должен быть списком"
            )
        
        # Асинхронная установка данных
        await asyncio.get_event_loop().run_in_executor(
            None, schedule_manager.set_data, data['days'], data['timeslots']
        )
        
        logger.info(f"✅ Данные успешно установлены: {len(data['days'])} дней, {len(data['timeslots'])} слотов")
        
        return {
            "message": "Данные успешно установлены и проиндексированы",
            "summary": {
                "total_days": len(schedule_manager.days),
                "total_timeslots": len(schedule_manager.timeslots),
                "interval_trees_built": len(schedule_manager.interval_trees)
            },
            "optimization": {
                "status": "active",
                "type": "interval-tree"
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Ошибка валидации данных: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка установки данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка установки данных: {str(e)}")


@app.get("/api/v1/busy/{date}")
async def get_busy_intervals(date: str):
    """
    Получить занятые промежутки для указанной даты.
    """
    try:
        intervals = schedule_manager.get_busy_intervals(date)
        
        return {
            "date": date,
            "busy_intervals": intervals,
            "count": len(intervals),
            "working_day": True,
            "optimization": "interval-tree"
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения занятых промежутков для {date}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/free/{date}")
async def get_free_time(date: str):
    """
    Получить свободное время для указанной даты.
    """
    try:
        intervals = schedule_manager.get_free_time(date)

        total_free_minutes = 0
        for start_str, end_str in intervals:
            start_time = schedule_manager._parse_time(start_str)
            end_time = schedule_manager._parse_time(end_str)
            duration = schedule_manager._time_to_minutes(end_time) - schedule_manager._time_to_minutes(start_time)
            total_free_minutes += duration
        
        return {
            "date": date,
            "free_intervals": intervals,
            "count": len(intervals),
            "total_free_hours": total_free_minutes / 60,
            "optimization": "interval-tree"
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения свободного времени для {date}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/available/{date}")
async def check_availability(
    date: str, 
    start_time: str = Query(..., description="Время начала в формате HH:MM"),
    end_time: str = Query(..., description="Время окончания в формате HH:MM")
):
    """
    Проверить доступность промежутка времени.
    """
    try:
        is_available = schedule_manager.is_time_available(date, start_time, end_time)
        
        response_data = {
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "available": is_available,
            "message": "Время доступно для бронирования" if is_available else "Время уже занято",
            "optimization": "interval-tree-search"
        }
        
        if not is_available:
            try:
                free_intervals = schedule_manager.get_free_time(date)
                nearby_slots = []
                
                for free_start, free_end in free_intervals:
                    nearby_slots.append({
                        "start": free_start,
                        "end": free_end
                    })
                
                response_data["suggestions"] = {
                    "message": "Альтернативные свободные промежутки:",
                    "free_slots": nearby_slots[:5]
                }
                
            except Exception:
                pass  
        
        return response_data
        
    except Exception as e:
        logger.error(f"Ошибка проверки доступности для {date} {start_time}-{end_time}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/find-slot/{date}")
async def find_free_slot(
    date: str,
    duration_minutes: int = Query(..., description="Продолжительность в минутах", gt=0)
):
    """
    Найти свободный промежуток указанной продолжительности.
    """
    try:
        start_time = schedule_manager.find_free_slot(date, duration_minutes)
        
        response_data = {
            "date": date,
            "duration_minutes": duration_minutes,
            "duration_hours": duration_minutes / 60,
            "found": start_time is not None,
            "optimization": "interval-tree"
        }
        
        if start_time:
            start_obj = schedule_manager._parse_time(start_time)
            end_minutes = schedule_manager._time_to_minutes(start_obj) + duration_minutes
            end_time = schedule_manager._minutes_to_time(end_minutes).strftime('%H:%M')
            
            response_data.update({
                "slot": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": duration_minutes
                },
                "message": f"Найден свободный слот с {start_time} до {end_time}"
            })
        else:
            try:
                free_intervals = schedule_manager.get_free_time(date)
                alternatives = []
                
                for free_start, free_end in free_intervals:
                    start_obj = schedule_manager._parse_time(free_start)
                    end_obj = schedule_manager._parse_time(free_end)
                    available_duration = schedule_manager._time_to_minutes(end_obj) - schedule_manager._time_to_minutes(start_obj)
                    
                    alternatives.append({
                        "start": free_start,
                        "end": free_end,
                        "available_minutes": available_duration,
                        "available_hours": available_duration / 60
                    })
                
                response_data.update({
                    "message": f"Слот на {duration_minutes} минут не найден",
                    "alternatives": {
                        "message": "Доступные свободные промежутки:",
                        "slots": alternatives
                    }
                })
                
            except Exception:
                response_data["message"] = f"Слот на {duration_minutes} минут не найден"
        
        return response_data
        
    except Exception as e:
        logger.error(f"Ошибка поиска слота для {date} на {duration_minutes} минут: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/stats")
async def get_statistics():
    """
    📊 Получить статистику производительности и использования.
    
    Возвращает детальную информацию о:
    - Производительности операций
    - Статистике деревьев
    - Использовании кэша (если доступен)
    """
    try:
        base_stats = {
            "data_summary": {
                "total_days": len(schedule_manager.days),
                "total_timeslots": len(schedule_manager.timeslots),
                "indexed_dates": len(schedule_manager.interval_trees),
                "trees_active": len(schedule_manager.interval_trees) > 0
            },
            "optimization": {
                "type": "interval-tree",
                "status": "active",
                "complexity": {
                    "search": "O(log n)",
                    "insert": "O(log n)", 
                    "query": "O(k) where k = slots per day"
                }
            }
        }
        
        if hasattr(schedule_manager, 'get_statistics'):
            extended_stats = schedule_manager.get_statistics()
            if extended_stats:
                base_stats.update(extended_stats)
        
        if schedule_manager.interval_trees:
            tree_info = {}
            for date, tree in list(schedule_manager.interval_trees.items())[:5]:  # Первые 5 дат
                tree_info[date] = {
                    "size": tree.size,
                    "empty": tree.is_empty()
                }
            
            base_stats["trees_sample"] = tree_info
            base_stats["trees_total"] = len(schedule_manager.interval_trees)
        
        return base_stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


# ==========================================
# Legacy endpoints (для совместимости)
# ==========================================

@app.get("/busy/{date}")
async def get_busy_intervals_v1(date: str):
    return await get_busy_intervals(date)


@app.get("/free/{date}")
async def get_free_time_v1(date: str):
    return await get_free_time(date)


@app.get("/available/{date}")
async def check_availability_v1(date: str, start_time: str, end_time: str):
    return await check_availability(date, start_time, end_time)


@app.get("/find-slot/{date}")
async def find_free_slot_v1(date: str, duration_minutes: int):
    return await find_free_slot(date, duration_minutes)


def main():
    os.makedirs("logs", exist_ok=True)
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("RELOAD", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info(f"Запуск Schedule Manager")
    logger.info(f"Конфигурация: host={host}, port={port}, log_level={log_level}")
    
    if reload:
        logger.info("🔄 Режим разработки: hot-reload включен")
        
    uvicorn.run(
        "schedule_manager.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        workers=workers if not reload else 1,
        access_log=True,
        loop="auto"
    )


if __name__ == "__main__":
    main()