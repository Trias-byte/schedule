"""
Исправленная версия core.py с фиксом IntervalTree
Основные изменения:
1. Добавлена проверка на None в _update_max_end
2. Исправлена логика инициализации корня дерева
3. Добавлены дополнительные проверки безопасности
"""

import datetime
import requests
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    RED = "red"
    BLACK = "black"


@dataclass
class IntervalNode:
    start: int  # Время начала в минутах
    end: int    # Время окончания в минутах
    slot_id: int  # ID слота
    max_end: int  # Максимальный end в поддереве
    
    left: Optional['IntervalNode'] = None
    right: Optional['IntervalNode'] = None
    parent: Optional['IntervalNode'] = None
    color: Color = Color.RED
    
    def __post_init__(self):
        if self.max_end == 0:
            self.max_end = self.end
    
    def overlaps_with(self, start: int, end: int) -> bool:
        return not (self.end <= start or self.start >= end)


class IntervalTree:    
    def __init__(self):
        self.root: Optional[IntervalNode] = None
        self.nil = IntervalNode(0, 0, -1, 0, color=Color.BLACK)
        self.size = 0
    
    def _update_max_end(self, node: IntervalNode) -> None:
        # Добавляем проверку на None - это ключевое исправление!
        if node is None or node == self.nil:
            return
        
        node.max_end = node.end
        if node.left is not None and node.left != self.nil:
            node.max_end = max(node.max_end, node.left.max_end)
        if node.right is not None and node.right != self.nil:
            node.max_end = max(node.max_end, node.right.max_end)
    
    def _left_rotate(self, x: IntervalNode) -> None:
        if x is None or x.right is None:
            return
            
        y = x.right
        x.right = y.left
        
        if y.left != self.nil:
            y.left.parent = x
        
        y.parent = x.parent
        
        if x.parent is None or x.parent == self.nil:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        
        y.left = x
        x.parent = y
        
        self._update_max_end(x)
        self._update_max_end(y)
    
    def _right_rotate(self, y: IntervalNode) -> None:
        if y is None or y.left is None:
            return
            
        x = y.left
        y.left = x.right
        
        if x.right != self.nil:
            x.right.parent = y
        
        x.parent = y.parent
        
        if y.parent is None or y.parent == self.nil:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        
        x.right = y
        y.parent = x
        
        self._update_max_end(y)
        self._update_max_end(x)
    
    def _insert_fixup(self, node: IntervalNode) -> None:
        if node is None:
            return
            
        while (node.parent is not None and 
               node.parent != self.nil and 
               node.parent.color == Color.RED):
            
            if (node.parent.parent is None or 
                node.parent == node.parent.parent.left):
                
                uncle = (node.parent.parent.right 
                        if node.parent.parent is not None 
                        else self.nil)
                
                if uncle is not None and uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    if node.parent.parent is not None:
                        node.parent.parent.color = Color.RED
                        node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self._left_rotate(node)
                    
                    if node.parent is not None:
                        node.parent.color = Color.BLACK
                        if node.parent.parent is not None:
                            node.parent.parent.color = Color.RED
                            self._right_rotate(node.parent.parent)
            else:
                uncle = (node.parent.parent.left 
                        if node.parent.parent is not None 
                        else self.nil)
                
                if uncle is not None and uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    if node.parent.parent is not None:
                        node.parent.parent.color = Color.RED
                        node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._right_rotate(node)
                    
                    if node.parent is not None:
                        node.parent.color = Color.BLACK
                        if node.parent.parent is not None:
                            node.parent.parent.color = Color.RED
                            self._left_rotate(node.parent.parent)
        
        if self.root is not None:
            self.root.color = Color.BLACK
    
    def insert(self, start: int, end: int, slot_id: int) -> None:
        new_node = IntervalNode(start, end, slot_id, end)
        new_node.left = self.nil
        new_node.right = self.nil
        new_node.parent = self.nil
        
        current = self.root
        parent = self.nil
        
        # Исправляем логику - проверяем на None
        while current is not None and current != self.nil:
            parent = current
            self._update_max_end(current)
            
            if new_node.start <= current.start:
                current = current.left
            else:
                current = current.right
        
        new_node.parent = parent
        
        if parent == self.nil or parent is None:
            self.root = new_node
        elif new_node.start <= parent.start:
            parent.left = new_node
        else:
            parent.right = new_node
        
        # Обновляем max_end для всех предков
        node = new_node
        while node is not None and node != self.nil:
            self._update_max_end(node)
            node = node.parent
        
        self._insert_fixup(new_node)
        self.size += 1
    
    def find_overlapping(self, start: int, end: int) -> List[int]:
        result = []
        
        def search(node: IntervalNode) -> None:
            if node is None or node == self.nil:
                return
            
            if node.overlaps_with(start, end):
                result.append(node.slot_id)
            
            if (node.left is not None and 
                node.left != self.nil and 
                node.left.max_end > start):
                search(node.left)
            
            if (node.right is not None and 
                node.right != self.nil and 
                node.start < end):
                search(node.right)
        
        if self.root is not None:
            search(self.root)
        
        return result
    
    def get_all_intervals(self) -> List[Tuple[int, int, int]]:
        result = []
        
        def inorder(node: IntervalNode) -> None:
            if node is None or node == self.nil:
                return
            
            inorder(node.left)
            result.append((node.start, node.end, node.slot_id))
            inorder(node.right)
        
        if self.root is not None:
            inorder(self.root)
        
        return sorted(result)
    
    def is_empty(self) -> bool:
        return self.root is None or self.root == self.nil


@dataclass
class Day:
    id: int
    date: datetime.date
    start: datetime.time
    end: datetime.time
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Day':
        return cls(
            id=data['id'],
            date=datetime.datetime.strptime(data['date'], '%Y-%m-%d').date(),
            start=datetime.datetime.strptime(data['start'], '%H:%M').time(),
            end=datetime.datetime.strptime(data['end'], '%H:%M').time()
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'start': self.start.strftime('%H:%M'),
            'end': self.end.strftime('%H:%M')
        }
    
    def is_working_time(self, time: datetime.time) -> bool:
        return self.start <= time <= self.end


@dataclass
class TimeSlot:
    id: int
    day_id: int
    start: datetime.time
    end: datetime.time
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TimeSlot':
        return cls(
            id=data['id'],
            day_id=data['day_id'],
            start=datetime.datetime.strptime(data['start'], '%H:%M').time(),
            end=datetime.datetime.strptime(data['end'], '%H:%M').time()
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'day_id': self.day_id,
            'start': self.start.strftime('%H:%M'),
            'end': self.end.strftime('%H:%M')
        }
    
    def duration_minutes(self) -> int:
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        return end_minutes - start_minutes
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        return not (self.end <= other.start or self.start >= other.end)


class ScheduleManager:   
    def __init__(self, endpoint_url: str = "https://ofc-test-01.tspb.su/test-task/"):
        self.endpoint_url = endpoint_url
        self.days: List[Day] = []
        self.timeslots: List[TimeSlot] = []
        
        # Индексы для быстрого доступа
        self.day_by_date: Dict[str, Day] = {}
        self.day_by_id: Dict[int, Day] = {}
        
        # Interval Trees для каждой даты
        self.interval_trees: Dict[str, IntervalTree] = {}
        
    def load_data(self) -> None:
        try:
            response = requests.get(self.endpoint_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.days = [Day.from_dict(day_data) for day_data in data['days']]
            self.timeslots = [TimeSlot.from_dict(slot_data) for slot_data in data['timeslot']]
            
            self._build_indexes()
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ошибка при загрузке данных: {e}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Неверный формат данных: {e}")
    
    def set_data(self, days: List[dict], timeslots: List[dict]) -> None:
        try:
            self.days = [Day.from_dict(day_data) for day_data in days]
            self.timeslots = [TimeSlot.from_dict(slot_data) for slot_data in timeslots]
            
            self._build_indexes()
            
        except (KeyError, ValueError) as e:
            raise ValueError(f"Неверный формат данных: {e}")
    
    def _build_indexes(self) -> None:
        self.day_by_date.clear()
        self.day_by_id.clear()
        self.interval_trees.clear()
        
        # Индексация дней
        for day in self.days:
            date_str = day.date.strftime('%Y-%m-%d')
            self.day_by_date[date_str] = day
            self.day_by_id[day.id] = day
        
        # Построение деревьев интервалов
        for slot in self.timeslots:
            day = self.day_by_id.get(slot.day_id)
            if not day:
                continue
                
            date_str = day.date.strftime('%Y-%m-%d')
            
            if date_str not in self.interval_trees:
                self.interval_trees[date_str] = IntervalTree()
            
            start_minutes = self._time_to_minutes(slot.start)
            end_minutes = self._time_to_minutes(slot.end)
            
            self.interval_trees[date_str].insert(start_minutes, end_minutes, slot.id)
    
    def _get_day_by_date(self, date: datetime.date) -> Optional[Day]:
        date_str = date.strftime('%Y-%m-%d')
        return self.day_by_date.get(date_str)
    
    def _parse_date(self, date_str: str) -> datetime.date:
        try:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Неверный формат даты: {date_str}. Ожидается: yyyy-mm-dd")
    
    def _parse_time(self, time_str: str) -> datetime.time:
        try:
            return datetime.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            raise ValueError(f"Неверный формат времени: {time_str}. Ожидается: HH:MM")
    
    def _time_to_minutes(self, time_obj: datetime.time) -> int:
        """Преобразует время в минуты с начала дня."""
        return time_obj.hour * 60 + time_obj.minute
    
    def _minutes_to_time(self, minutes: int) -> datetime.time:
        return datetime.time(hour=minutes // 60, minute=minutes % 60)
    
    def get_busy_intervals(self, date_str: str) -> List[Tuple[str, str]]:
        if not self.days:
            raise RuntimeError("Данные не загружены. Вызовите load_data() или set_data()")
        
        date = self._parse_date(date_str)
        day = self._get_day_by_date(date)
        
        if not day:
            raise RuntimeError(f"Рабочий день для даты {date_str} не найден")
        
        tree = self.interval_trees.get(date_str)
        if not tree or tree.is_empty():
            return []
        
        intervals = tree.get_all_intervals()
        return [
            (self._minutes_to_time(start).strftime('%H:%M'),
             self._minutes_to_time(end).strftime('%H:%M'))
            for start, end, _ in intervals
        ]
    
    def get_free_time(self, date_str: str) -> List[Tuple[str, str]]:
        if not self.days:
            raise RuntimeError("Данные не загружены. Вызовите load_data() или set_data()")
        
        date = self._parse_date(date_str)
        day = self._get_day_by_date(date)
        
        if not day:
            raise RuntimeError(f"Рабочий день для даты {date_str} не найден")
        
        tree = self.interval_trees.get(date_str)
        day_start = self._time_to_minutes(day.start)
        day_end = self._time_to_minutes(day.end)
        
        if not tree or tree.is_empty():
            return [(day.start.strftime('%H:%M'), day.end.strftime('%H:%M'))]
        
        intervals = tree.get_all_intervals()
        gaps = []
        current_time = day_start
        
        for start, end, _ in intervals:
            if current_time < start:
                gaps.append((current_time, start))
            current_time = max(current_time, end)
        
        if current_time < day_end:
            gaps.append((current_time, day_end))
        
        return [
            (self._minutes_to_time(start).strftime('%H:%M'),
             self._minutes_to_time(end).strftime('%H:%M'))
            for start, end in gaps
        ]
    
    def is_time_available(self, date_str: str, start_time_str: str, end_time_str: str) -> bool:
        if not self.days:
            raise RuntimeError("Данные не загружены. Вызовите load_data() или set_data()")
        
        date = self._parse_date(date_str)
        start_time = self._parse_time(start_time_str)
        end_time = self._parse_time(end_time_str)
        
        if start_time >= end_time:
            raise ValueError("Время начала должно быть меньше времени окончания")
        
        day = self._get_day_by_date(date)
        if not day:
            raise RuntimeError(f"Рабочий день для даты {date_str} не найден")
        
        if start_time < day.start or end_time > day.end:
            return False
        
        tree = self.interval_trees.get(date_str)
        if not tree or tree.is_empty():
            return True
        
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = self._time_to_minutes(end_time)
        
        overlapping = tree.find_overlapping(start_minutes, end_minutes)
        return len(overlapping) == 0
    
    def find_free_slot(self, date_str: str, duration_minutes: int) -> Optional[str]:
        if duration_minutes <= 0:
            raise ValueError("Продолжительность должна быть положительной")
        
        free_intervals = self.get_free_time(date_str)
        
        for start_str, end_str in free_intervals:
            start_time = self._parse_time(start_str)
            end_time = self._parse_time(end_str)
            
            interval_duration = self._time_to_minutes(end_time) - self._time_to_minutes(start_time)
            
            if interval_duration >= duration_minutes:
                return start_str
        
        return None