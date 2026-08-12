"""Lifetime grid energy totals, reported as 32-bit floats."""

from __future__ import annotations

from modbus_connection.model import float32

from .model import EnertechComponent


class Energy(EnertechComponent):
    """Total energy imported from and exported to the grid."""

    grid_import = float32(0x152, unit="kWh")
    grid_export = float32(0x154, unit="kWh")
