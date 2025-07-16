__version__ = "1.0.0"
__author__ = "Trias-Byte"
__email__ = "triasfreelance@gmail.com"

from .core import ScheduleManager, Day, TimeSlot
from .main import app

__all__ = [
    "ScheduleManager",
    "Day", 
    "TimeSlot",
    "app",
    "__version__",
]