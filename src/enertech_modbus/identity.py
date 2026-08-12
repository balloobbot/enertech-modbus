"""Static identity: serial number and how the unit is built.

None of this changes while the unit runs, so it is read once during setup rather
than on every poll.

The plugin reads the serial number from 0x14 and, if that read fails, retries at
0x300 with a byte swap to work around a decoder bug it no longer has. Only 0x14
is modelled here.
"""

from __future__ import annotations

from modbus_connection.model import enum, string

from .enums import Configuration, ProductType
from .model import EnertechComponent


class Identity(EnertechComponent):
    """Serial number, product type and phase configuration."""

    serial_number = string(0x14, 4)
    product_type = enum(0x108, ProductType)
    configuration = enum(0x109, Configuration)
    """Input/output phase wiring, and standalone vs parallel operation."""
