"""The battery bank."""

from __future__ import annotations

from .model import EnertechComponent, scaled, unscaled


class Battery(EnertechComponent):
    """Battery voltage, currents and state of charge."""

    voltage = scaled(0x130, 0.1, unit="V")
    capacity = unscaled(0x133, unit="%")
    """State of charge."""

    current_in = scaled(0x134, 0.1, unit="A")
    current = scaled(0x135, 0.1, unit="A")
    charge_current_pv = scaled(0x224, 0.1, unit="A")
    """Charge current coming from PV."""
