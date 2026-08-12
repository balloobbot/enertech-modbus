"""An Enertech inverter over modbus-connection's in-memory mock backend.

The mock ships with ``modbus-connection`` as an auto-registered pytest plugin,
so there is no server, socket or backend here — just an address-keyed store
seeded with Enertech-shaped register values. Everything is a holding register.
"""

from __future__ import annotations

import struct

import pytest
from modbus_connection.mock import MockModbusUnit

from enertech_modbus import EnertechInverter


def ascii_words(text: str) -> list[int]:
    """Pack ASCII into 16-bit registers, two characters per register."""
    if len(text) % 2:
        text += "\0"
    return [(ord(text[i]) << 8) | ord(text[i + 1]) for i in range(0, len(text), 2)]


def float32_words(value: float) -> list[int]:
    """Encode an IEEE-754 single as two big-endian 16-bit registers."""
    high, low = struct.unpack(">HH", struct.pack(">f", value))
    return [high, low]


# Raw holding-register words keyed by address; the decoded value is inline.
HOLDING: dict[int, int | list[int]] = {
    # -- identity --
    0x14: ascii_words("ENT12345"),  # serial number
    0x108: 3,  # product type -> SOLAR_POWER_UNIT
    0x109: 3,  # configuration -> PHASE3_IN_PHASE3_OUT_STANDALONE
    # -- status --
    0x10E: 1,  # MPPT mode -> AUTO
    0x10F: 3,  # inverter mode -> EXPORT
    # -- grid --
    0x111: 240,  # voltage R
    0x112: 241,  # voltage Y
    0x113: 239,  # voltage B
    0x114: 105,  # current R -> 10.5 A
    0x115: 110,  # current Y -> 11.0 A
    0x116: 98,  # current B -> 9.8 A
    0x119: 98,  # input power factor -> 0.98
    0x11A: 500,  # frequency -> 50.0 Hz
    # -- inverter stage --
    0x11B: 230,  # voltage R
    0x11C: 231,  # voltage Y
    0x11D: 229,  # voltage B
    0x11E: 150,  # current R -> 15.0 A
    0x11F: 152,  # current Y -> 15.2 A
    0x120: 148,  # current B -> 14.8 A
    0x124: 499,  # frequency -> 49.9 Hz
    # -- output --
    0x125: 230,  # voltage R
    0x126: 230,  # voltage Y
    0x127: 231,  # voltage B
    0x128: 90,  # load current R -> 9.0 A
    0x129: 91,  # load current Y -> 9.1 A
    0x12A: 89,  # load current B -> 8.9 A
    0x12D: 95,  # output power factor -> 0.95
    0x12E: 501,  # frequency -> 50.1 Hz
    0x12F: 42,  # load -> 42 %
    # -- battery --
    0x130: 532,  # voltage -> 53.2 V
    0x133: 87,  # capacity -> 87 %
    0x134: 210,  # current in -> 21.0 A
    0x135: 205,  # current -> 20.5 A
    0x224: 143,  # PV charge current -> 14.3 A
    # -- solar --
    0x13B: 380,  # string 1 voltage
    0x13C: 62,  # string 1 current -> 6.2 A
    0x13D: 375,  # string 2 voltage
    0x13E: 58,  # string 2 current -> 5.8 A
    0x142: 2175,  # string 2 power -> 2175 W
    0x146: [0, 12345],  # string 1 energy -> 1234.5 kWh (uint32, big word order)
    # -- energy --
    0x152: float32_words(4567.5),  # grid import kWh
    0x154: float32_words(890.25),  # grid export kWh
    # -- faults: every stage healthy --
    0x159: 500,  # monitor -> NO_ERROR
    0x15A: 100,  # grid -> NO_ERROR
    0x15B: 600,  # PFC -> NO_ERROR
    0x15C: 600,  # solar -> NO_ERROR
    0x15D: 400,  # inverter -> NO_ERROR
    0x15E: 300,  # battery -> NO_ERROR
    # -- run-time counters --
    0x15F: 1234,  # inverter run time -> 1234 h
    0x160: 56,  # bypass run time -> 56 h
    0x161: 12,  # grid fail -> 12 h
    0x162: 34,  # grid fail -> 34 min
    # -- temperatures --
    0x136: 47,  # DC-DC -> 47 °C
    0x169: 385,  # DC-AC -> 38.5 °C
    0x222: 421,  # transformer -> 42.1 °C
    # -- control --
    0x196: 0x49,  # command word: bits 0, 3 and 6 set
    0x197: 63,  # generator current limit -> 63 A
    0x198: 120,  # generator run time -> 120 min
    0x199: 48,  # generator start voltage -> 48 V
    0x1A5: 3,  # mode setting -> EXPORT
}


@pytest.fixture
def inverter(mock_modbus_unit: MockModbusUnit) -> EnertechInverter:
    """An EnertechInverter over the mock unit, preloaded with device values."""
    mock_modbus_unit.holding.update(HOLDING)
    return EnertechInverter(mock_modbus_unit)
