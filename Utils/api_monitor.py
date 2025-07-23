"""
API Usage Monitoring Utility
Helps track and monitor API usage patterns and rate limiting
"""

import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class APIUsageMonitor:
    """Monitor API usage patterns and provide insights"""

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.request_log = deque()
        self.error_log = deque()
        self.lock = threading.Lock()

        # Statistics
        self.total_requests = 0
        self.rate_limit_errors = 0
        self.server_errors = 0
        self.successful_requests = 0

    def log_request(
        self,
        status: str,
        error_type: Optional[str] = None,
        response_time: Optional[float] = None,
    ):
        """Log an API request"""
        with self.lock:
            timestamp = time.time()

            # Clean old entries
            self._clean_old_entries()

            # Log the request
            entry = {
                "timestamp": timestamp,
                "status": status,
                "error_type": error_type,
                "response_time": response_time,
            }

            self.request_log.append(entry)
            self.total_requests += 1

            # Update counters
            if status == "success":
                self.successful_requests += 1
            elif error_type == "rate_limit":
                self.rate_limit_errors += 1
            elif error_type == "server_error":
                self.server_errors += 1

    def _clean_old_entries(self):
        """Remove entries older than the window"""
        cutoff_time = time.time() - (self.window_minutes * 60)

        while self.request_log and self.request_log[0]["timestamp"] < cutoff_time:
            self.request_log.popleft()

    def get_current_stats(self) -> Dict:
        """Get current usage statistics"""
        with self.lock:
            self._clean_old_entries()

            recent_requests = len(self.request_log)
            recent_rate_limits = sum(
                1
                for entry in self.request_log
                if entry.get("error_type") == "rate_limit"
            )
            recent_errors = sum(
                1 for entry in self.request_log if entry["status"] != "success"
            )

            avg_response_time = None
            response_times = [
                entry["response_time"]
                for entry in self.request_log
                if entry.get("response_time") is not None
            ]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)

            return {
                "total_requests_lifetime": self.total_requests,
                "recent_requests": recent_requests,
                "recent_rate_limit_errors": recent_rate_limits,
                "recent_total_errors": recent_errors,
                "success_rate_recent": (
                    (recent_requests - recent_errors) / recent_requests * 100
                    if recent_requests > 0
                    else 0
                ),
                "avg_response_time": avg_response_time,
                "requests_per_minute": recent_requests / self.window_minutes,
                "window_minutes": self.window_minutes,
            }

    def should_throttle(self, threshold_requests_per_minute: int = 25) -> bool:
        """Check if we should throttle requests based on recent activity"""
        with self.lock:
            self._clean_old_entries()
            requests_per_minute = len(self.request_log) / self.window_minutes
            return requests_per_minute >= threshold_requests_per_minute

    def get_throttle_delay(self) -> float:
        """Get recommended delay before next request"""
        with self.lock:
            self._clean_old_entries()

            # If we have recent rate limit errors, suggest longer delay
            recent_rate_limits = sum(
                1
                for entry in self.request_log
                if entry.get("error_type") == "rate_limit"
            )

            if recent_rate_limits > 0:
                return min(10.0, recent_rate_limits * 2.0)  # Max 10 seconds

            # Base throttling on request rate
            requests_per_minute = len(self.request_log) / self.window_minutes
            if requests_per_minute > 20:
                return 3.0
            elif requests_per_minute > 15:
                return 1.0

            return 0.0

    def log_summary(self):
        """Log a summary of current stats"""
        stats = self.get_current_stats()
        logger.info(
            f"API Usage Stats: {stats['recent_requests']} requests in last {self.window_minutes}min, "
            f"{stats['success_rate_recent']:.1f}% success rate, "
            f"{stats['recent_rate_limit_errors']} rate limit errors"
        )


# Global monitor instance
api_monitor = APIUsageMonitor(window_minutes=5)


def log_api_request(
    status: str, error_type: Optional[str] = None, response_time: Optional[float] = None
):
    """Helper function to log API requests"""
    api_monitor.log_request(status, error_type, response_time)


def get_api_stats() -> Dict:
    """Helper function to get API stats"""
    return api_monitor.get_current_stats()


def should_throttle_requests() -> bool:
    """Helper function to check if requests should be throttled"""
    return api_monitor.should_throttle()


def get_recommended_delay() -> float:
    """Helper function to get recommended delay"""
    return api_monitor.get_throttle_delay()
