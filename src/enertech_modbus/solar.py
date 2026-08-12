"""The PV strings.

The plugin declares a power register for string 2 only, and for string 1 a
32-bit lifetime energy total it names "Solar Power 1" while giving it energy
units. Both are carried over as declared.
"""

from __future__ import annotations

from modbus_connection.model import uint32

from .model import EnertechComponent, scaled, unscaled


class Solar(EnertechComponent):
    """PV string voltages and currents, string 2 power, string 1 total energy."""

    voltage_1 = unscaled(0x13B, unit="V")
    current_1 = scaled(0x13C, 0.1, unit="A")
    voltage_2 = unscaled(0x13D, unit="V")
    current_2 = scaled(0x13E, 0.1, unit="A")
    power_2 = unscaled(0x142, unit="W")
    energy_1 = uint32(0x146, scale=0.1, unit="kWh")
    """Lifetime energy from string 1."""
