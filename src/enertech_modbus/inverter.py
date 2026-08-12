"""The inverter stage itself, between the DC bus and the output."""

from __future__ import annotations

from .model import EnertechComponent, scaled, unscaled


class Inverter(EnertechComponent):
    """Inverter-stage voltages, currents and frequency."""

    voltage_r = unscaled(0x11B, unit="V")
    voltage_y = unscaled(0x11C, unit="V")
    voltage_b = unscaled(0x11D, unit="V")
    current_r = scaled(0x11E, 0.1, unit="A")
    current_y = scaled(0x11F, 0.1, unit="A")
    current_b = scaled(0x120, 0.1, unit="A")
    frequency = scaled(0x124, 0.1, unit="Hz")
