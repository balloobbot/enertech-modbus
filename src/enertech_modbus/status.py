"""Operating mode and the lifetime run-time counters."""

from __future__ import annotations

from modbus_connection.model import enum

from .enums import InverterMode, MPPTMode
from .model import EnertechComponent, unscaled


class Status(EnertechComponent):
    """What the inverter is doing, and how long it has been doing it."""

    mppt_mode = enum(0x10E, MPPTMode)
    mode = enum(0x10F, InverterMode)
    """The mode the inverter is running in; set it via ``Control.mode``."""

    inverter_run_time = unscaled(0x15F, unit="h")
    bypass_run_time = unscaled(0x160, unit="h")
    grid_fail_hours = unscaled(0x161, unit="h")
    grid_fail_minutes = unscaled(0x162, unit="min")
    """The minutes part of the total grid-failure time counted by 0x161."""
