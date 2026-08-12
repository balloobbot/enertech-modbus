"""The six fault registers, one per stage."""

from __future__ import annotations

from modbus_connection.model import enum

from .enums import (
    BatteryFault,
    GridFault,
    InverterFault,
    MonitorFault,
    PFCFault,
    SolarFault,
)
from .model import EnertechComponent


class Faults(EnertechComponent):
    """The current fault code of each stage.

    Each register reports one code at a time, not a bitmask, and each has its own
    "no error" value — so a healthy unit reads e.g. ``MonitorFault.NO_ERROR``
    rather than ``None``. An unrecognised code decodes to ``None``.
    """

    monitor = enum(0x159, MonitorFault)
    grid = enum(0x15A, GridFault)
    pfc = enum(0x15B, PFCFault)
    solar = enum(0x15C, SolarFault)
    inverter = enum(0x15D, InverterFault)
    battery = enum(0x15E, BatteryFault)

    @property
    def healthy(self) -> bool:
        """True when every stage reports its own "no error" code."""
        return (
            self.monitor is MonitorFault.NO_ERROR
            and self.grid is GridFault.NO_ERROR
            and self.pfc is PFCFault.NO_ERROR
            and self.solar is SolarFault.NO_ERROR
            and self.inverter is InverterFault.NO_ERROR
            and self.battery is BatteryFault.NO_ERROR
        )
