"""Writable settings and the command word.

These registers are not part of a poll: the plugin declares them as write-only
entities and never reads them back, so this component is refreshed on demand
(``await device.control.async_update()``) rather than by ``async_update()``.

The sixteen bits of the command word 0x196 are transcribed from the plugin's
switch declarations. Those switches carry no write function upstream, so they
never reach the device and the write semantics are untested: a bit here is
written as a read-modify-write of 0x196, which is what a latching control word
wants but not what a device expecting a pulse would.
"""

from __future__ import annotations

from collections.abc import Callable

from modbus_connection.model import bit, enum

from .enums import InverterMode
from .model import EnertechComponent, unscaled


def _between(low: int, high: int) -> Callable[[int], int]:
    """Reject a write outside the range the plugin allows for the setting."""

    def validate(value: int) -> int:
        if not low <= value <= high:
            raise ValueError(f"value must be between {low} and {high}, got {value}")
        return value

    return validate


class Control(EnertechComponent):
    """Generator settings, the operating-mode setting and the command bits."""

    generator_current_limit = unscaled(0x197, unit="A", writable=_between(10, 100))
    """Grid / diesel generator current limit (10-100 A)."""

    generator_run_time = unscaled(0x198, unit="min", writable=_between(10, 300))
    """How long the diesel generator runs once started (10-300 min)."""

    generator_start_voltage = unscaled(0x199, unit="V", writable=_between(10, 100))
    """Battery voltage below which the diesel generator starts (10-100 V)."""

    mode = enum(0x1A5, InverterMode, writable=True)
    """The operating mode to run in; reported back by ``Status.mode``."""

    force_generator_start_stop = bit(0x196, 0, writable=True)
    generator_start_auto_manual = bit(0x196, 1, writable=True)
    inverter_reset = bit(0x196, 2, writable=True)
    inverter_start_stop = bit(0x196, 3, writable=True)
    buzzer_disable = bit(0x196, 4, writable=True)
    emergency_off = bit(0x196, 5, writable=True)
    mppt1_on_off = bit(0x196, 6, writable=True)
    mppt2_on_off = bit(0x196, 7, writable=True)
    mppt3_on_off = bit(0x196, 8, writable=True)
    grid_charging_on_off = bit(0x196, 9, writable=True)
    export_on_off = bit(0x196, 10, writable=True)
    battery_test = bit(0x196, 11, writable=True)
    manual_equalize = bit(0x196, 12, writable=True)
    force_bypass_transfer = bit(0x196, 13, writable=True)
    auto_restart_enable_disable = bit(0x196, 14, writable=True)
    spare_3 = bit(0x196, 15, writable=True)
    """Undocumented upstream beyond its name."""

    async def set_mode(self, mode: InverterMode) -> None:
        """Set the operating mode."""
        await self.write("mode", mode)
