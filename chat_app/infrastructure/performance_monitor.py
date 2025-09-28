"""
Performance Monitoring Service
"""
import time
from typing import Dict, Optional

from chat_app.domain.value_objects import PerformanceMetrics


class PerformanceMonitor:
    """Performance monitoring for operations"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.checkpoints: Dict[str, float] = {}

    def start(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.checkpoints = {}

    def checkpoint(self, name: str):
        """Record a checkpoint"""
        if self.start_time:
            self.checkpoints[name] = time.time() - self.start_time

    def get_total_time(self) -> float:
        """Get total elapsed time"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0

    def get_metrics(self, operation: str) -> PerformanceMetrics:
        """Get performance metrics"""
        return PerformanceMetrics(
            total_time=self.get_total_time(),
            checkpoints=self.checkpoints.copy(),
            operation=operation,
        )

    def log_performance(self, operation: str):
        """Log performance metrics"""
        total_time = self.get_total_time()
        print(f"Performance - {operation}: {total_time:.2f}s")
        for name, time_taken in self.checkpoints.items():
            print(f"  {name}: {time_taken:.2f}s")


# Global performance monitor instance
perf_monitor = PerformanceMonitor()
