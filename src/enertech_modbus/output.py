"""The output (load) side."""

from __future__ import annotations

from .model import EnertechComponent, scaled, unscaled


class Output(EnertechComponent):
    """Output voltages, load currents, frequency, power factor and load level."""

    voltage_r = unscaled(0x125, unit="V")
    voltage_y = unscaled(0x126, unit="V")
    voltage_b = unscaled(0x127, unit="V")
    load_current_r = scaled(0x128, 0.1, unit="A")
    load_current_y = scaled(0x129, 0.1, unit="A")
    load_current_b = scaled(0x12A, 0.1, unit="A")
    power_factor = scaled(0x12D, 0.01)
    frequency = scaled(0x12E, 0.1, unit="Hz")
    load = unscaled(0x12F, unit="%")
    """Load level as a percentage of the unit's rating."""
