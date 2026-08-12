"""Writes: the mode select, the ranged generator settings, and the command bits."""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit

from enertech_modbus import EnertechInverter, InverterMode


async def test_set_mode(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await inverter.control.set_mode(InverterMode.BATTERY_LESS)
    assert await mock_modbus_unit.read_holding_registers(0x1A5, 1) == [4]


async def test_generator_settings_write_their_registers(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await inverter.control.write("generator_current_limit", 75)
    await inverter.control.write("generator_run_time", 240)
    await inverter.control.write("generator_start_voltage", 44)
    assert await mock_modbus_unit.read_holding_registers(0x197, 3) == [75, 240, 44]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("generator_current_limit", 9),  # below the 10-100 A range
        ("generator_current_limit", 101),
        ("generator_run_time", 301),  # above the 10-300 min range
        ("generator_start_voltage", 101),  # above the 10-100 V range
    ],
)
async def test_out_of_range_write_is_rejected(
    inverter: EnertechInverter,
    mock_modbus_unit: MockModbusUnit,
    field: str,
    value: int,
) -> None:
    """The validator rejects before anything reaches the device."""
    before = await mock_modbus_unit.read_holding_registers(0x197, 3)
    with pytest.raises(ValueError, match="must be between"):
        await inverter.control.write(field, value)
    assert await mock_modbus_unit.read_holding_registers(0x197, 3) == before


async def test_command_bit_write_leaves_the_other_bits_alone(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """A bit write is a read-modify-write of the whole command word."""
    assert await mock_modbus_unit.read_holding_registers(0x196, 1) == [0x49]

    await inverter.control.write("export_on_off", True)  # bit 10
    assert await mock_modbus_unit.read_holding_registers(0x196, 1) == [0x449]

    await inverter.control.write("inverter_start_stop", False)  # clears bit 3
    assert await mock_modbus_unit.read_holding_registers(0x196, 1) == [0x441]


async def test_read_only_fields_reject_writes(inverter: EnertechInverter) -> None:
    with pytest.raises(Exception, match="read-only"):
        await inverter.battery.write("capacity", 50)
