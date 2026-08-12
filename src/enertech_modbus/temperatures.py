"""Module temperatures.

The DC-DC reading is a whole-degree register while the other two are 0.1-scaled;
that difference is in the plugin and is preserved here.
"""

from __future__ import annotations

from .model import EnertechComponent, scaled, unscaled


class Temperatures(EnertechComponent):
    """DC-DC, DC-AC and transformer temperatures."""

    dc_dc = unscaled(0x136, unit="°C")
    dc_ac = scaled(0x169, 0.1, unit="°C")
    transformer = scaled(0x222, 0.1, unit="°C")
    """The plugin calls this "translator temperature"."""
