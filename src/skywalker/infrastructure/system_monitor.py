"""Native Windows system counters, with no architecture-specific Python dependency."""
import ctypes as c
from ctypes import wintypes as w
import os
import platform
import shutil
from pathlib import Path


class MemoryStatus(c.Structure):
    _fields_ = [("length", w.DWORD), ("load", w.DWORD)] + [
        (name, c.c_ulonglong) for name in
        ("total", "available", "page_total", "page_available", "virtual_total",
         "virtual_available", "extended")]


class PowerStatus(c.Structure):
    _fields_ = [(name, w.BYTE) for name in ("ac", "flag", "percent", "saver")] + [
        ("remaining", w.DWORD), ("full", w.DWORD)]


class SystemMonitor:
    def __init__(self, disk: Path) -> None:
        self.disk = disk
        self.previous: tuple[int, int] | None = None

    def sample(self) -> dict[str, str]:
        values = {"System": f"{platform.system()} {platform.release()} • {platform.machine()}"}
        try:
            usage = shutil.disk_usage(self.disk)
            values["Storage"] = f"{usage.free / 2**30:.1f} GiB free / {usage.total / 2**30:.1f} GiB"
        except OSError:
            values["Storage"] = "Unavailable"
        if os.name != "nt":
            return values | {"CPU": "Unavailable", "RAM": "Unavailable", "Battery": "Unavailable"}
        kernel = c.WinDLL("kernel32", use_last_error=True)
        idle, system, user = w.FILETIME(), w.FILETIME(), w.FILETIME()
        kernel.GetSystemTimes.argtypes = [c.POINTER(w.FILETIME)] * 3
        kernel.GetSystemTimes.restype = w.BOOL
        if kernel.GetSystemTimes(c.byref(idle), c.byref(system), c.byref(user)):
            ticks = lambda value: (value.dwHighDateTime << 32) | value.dwLowDateTime
            current = (ticks(idle), ticks(system) + ticks(user))
            values["CPU"] = "Sampling…"
            if self.previous and current[1] > self.previous[1]:
                busy = 100 * (1 - (current[0] - self.previous[0]) / (current[1] - self.previous[1]))
                values["CPU"] = f"{max(0, min(100, busy)):.1f}%"
            self.previous = current
        else:
            values["CPU"] = "Unavailable"
        memory = MemoryStatus()
        memory.length = c.sizeof(memory)
        kernel.GlobalMemoryStatusEx.argtypes = [c.POINTER(MemoryStatus)]
        kernel.GlobalMemoryStatusEx.restype = w.BOOL
        values["RAM"] = "Unavailable"
        if kernel.GlobalMemoryStatusEx(c.byref(memory)):
            values["RAM"] = f"{memory.load}% • {(memory.total - memory.available) / 2**30:.1f} / {memory.total / 2**30:.1f} GiB"
        power = PowerStatus()
        kernel.GetSystemPowerStatus.argtypes = [c.POINTER(PowerStatus)]
        kernel.GetSystemPowerStatus.restype = w.BOOL
        values["Battery"] = "Unavailable"
        if kernel.GetSystemPowerStatus(c.byref(power)):
            level = "Unknown" if power.percent == 255 else f"{power.percent}%"
            values["Battery"] = "No battery" if power.flag != 255 and power.flag & 128 else f"{level} • " + {0: "Battery power", 1: "Plugged in"}.get(power.ac, "Power source unknown")
        return values
