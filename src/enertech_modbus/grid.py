"""The grid (input) side.

Phases are labelled R/Y/B on the device; they are the L1/L2/L3 of a three-phase
supply. A single-phase unit reports only the R phase.
"""

from __future__ import annotations

from .model import EnertechComponent, scaled, unscaled


class Grid(EnertechComponent):
    """Incoming grid voltages, currents, frequency and power factor."""

    voltage_r = unscaled(0x111, unit="V")
    voltage_y = unscaled(0x112, unit="V")
    voltage_b = unscaled(0x113, unit="V")
    current_r = scaled(0x114, 0.1, unit="A")
    current_y = scaled(0x115, 0.1, unit="A")
    current_b = scaled(0x116, 0.1, unit="A")
    power_factor = scaled(0x119, 0.01)
    frequency = scaled(0x11A, 0.1, unit="Hz")
