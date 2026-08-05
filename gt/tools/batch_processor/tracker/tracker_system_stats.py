"""Dependency-free system utilization helpers for the tracker UI."""

import ctypes
import os
import time


class SystemStats:
    """Samples system-wide CPU and memory utilization on Windows."""

    def __init__(self):
        """Initializes sampling state."""
        self.previous_idle = None
        self.previous_total = None

    def sample(self):
        """Samples current CPU and memory use.

        Returns:
            dict: CPU percentage and memory byte values, or empty values when unsupported.
        """
        if os.name != "nt":
            return {"cpu_percent": None, "memory_used": None, "memory_total": None}
        return self._sample_windows()

    def _sample_windows(self):
        """Samples Windows system counters.

        Returns:
            dict: Windows CPU and memory utilization.
        """
        idle_time = ctypes.c_ulonglong()
        kernel_time = ctypes.c_ulonglong()
        user_time = ctypes.c_ulonglong()
        ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle_time), ctypes.byref(kernel_time), ctypes.byref(user_time)
        )
        total = kernel_time.value + user_time.value
        cpu_percent = None
        if self.previous_total is not None and total > self.previous_total:
            total_delta = total - self.previous_total
            idle_delta = idle_time.value - self.previous_idle
            cpu_percent = max(0.0, min(100.0, 100.0 * (1.0 - idle_delta / total_delta)))
        self.previous_idle = idle_time.value
        self.previous_total = total

        class MemoryStatus(ctypes.Structure):
            """Windows MEMORYSTATUSEX structure."""

            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        memory = MemoryStatus()
        memory.length = ctypes.sizeof(MemoryStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
        return {
            "cpu_percent": cpu_percent,
            "memory_used": memory.total_physical - memory.available_physical,
            "memory_total": memory.total_physical,
            "sampled_at": time.time(),
        }
