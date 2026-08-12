"""The Enertech-specific base component and its two register helpers.

Every register on this device is an unsigned 16-bit holding register unless a
field says otherwise, so the helpers below fix ``signed=False`` rather than
repeating it on fifty declarations.
"""

from __future__ import annotations

from modbus_connection.model import (
    Component,
    NumberField,
    WriteValidator,
    gauge,
    integer,
)

# The plugin polls this device with block_size=100, so a single read never spans
# more than 100 registers. It declares no block boundaries beyond that, so the
# planner is left to derive the blocks from the fields (no register_ranges).
MAX_READ_SPAN = 100


class EnertechComponent(Component):
    """An Enertech sub-system: holding registers, capped at a 100-register read."""

    max_span = MAX_READ_SPAN


def scaled(
    address: int, scale: float, *, unit: str | None = None
) -> NumberField[float]:
    """An unsigned 16-bit register with a scale factor."""
    return gauge(address, scale, signed=False, unit=unit)


def unscaled(
    address: int,
    *,
    unit: str | None = None,
    writable: bool | WriteValidator = False,
) -> NumberField[int]:
    """An unsigned 16-bit register read as-is."""
    return integer(address, signed=False, unit=unit, writable=writable)
