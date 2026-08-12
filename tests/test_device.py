"""Decode tests over the in-memory mock backend."""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit

from enertech_modbus import (
    BatteryFault,
    Configuration,
    EnertechInverter,
    InverterFault,
    InverterMode,
    MonitorFault,
    MPPTMode,
    ProductType,
)


async def test_identity(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    assert inverter.identity.serial_number == "ENT12345"
    assert inverter.identity.product_type is ProductType.SOLAR_POWER_UNIT
    assert (
        inverter.identity.configuration is Configuration.PHASE3_IN_PHASE3_OUT_STANDALONE
    )


async def test_status(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    status = inverter.status
    assert status.mppt_mode is MPPTMode.AUTO
    assert status.mode is InverterMode.EXPORT
    assert status.inverter_run_time == 1234
    assert status.bypass_run_time == 56
    assert status.grid_fail_hours == 12
    assert status.grid_fail_minutes == 34


async def test_grid(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    grid = inverter.grid
    assert grid.voltage_r == 240
    assert grid.voltage_y == 241
    assert grid.voltage_b == 239
    assert grid.current_r == pytest.approx(10.5)
    assert grid.current_y == pytest.approx(11.0)
    assert grid.current_b == pytest.approx(9.8)
    assert grid.power_factor == pytest.approx(0.98)
    assert grid.frequency == pytest.approx(50.0)


async def test_inverter_stage(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    stage = inverter.inverter
    assert (stage.voltage_r, stage.voltage_y, stage.voltage_b) == (230, 231, 229)
    assert stage.current_r == pytest.approx(15.0)
    assert stage.current_y == pytest.approx(15.2)
    assert stage.current_b == pytest.approx(14.8)
    assert stage.frequency == pytest.approx(49.9)


async def test_output(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    output = inverter.output
    assert (output.voltage_r, output.voltage_y, output.voltage_b) == (230, 230, 231)
    assert output.load_current_r == pytest.approx(9.0)
    assert output.load_current_y == pytest.approx(9.1)
    assert output.load_current_b == pytest.approx(8.9)
    assert output.power_factor == pytest.approx(0.95)
    assert output.frequency == pytest.approx(50.1)
    assert output.load == 42


async def test_battery(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    battery = inverter.battery
    assert battery.voltage == pytest.approx(53.2)
    assert battery.capacity == 87
    assert battery.current_in == pytest.approx(21.0)
    assert battery.current == pytest.approx(20.5)
    assert battery.charge_current_pv == pytest.approx(14.3)


async def test_solar(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    solar = inverter.solar
    assert solar.voltage_1 == 380
    assert solar.current_1 == pytest.approx(6.2)
    assert solar.voltage_2 == 375
    assert solar.current_2 == pytest.approx(5.8)
    assert solar.power_2 == 2175
    assert solar.energy_1 == pytest.approx(1234.5)  # uint32, big word order


async def test_energy_is_float32(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    assert inverter.energy.grid_import == pytest.approx(4567.5)
    assert inverter.energy.grid_export == pytest.approx(890.25)


async def test_temperatures(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    temperatures = inverter.temperatures
    assert temperatures.dc_dc == 47  # whole degrees, unlike the other two
    assert temperatures.dc_ac == pytest.approx(38.5)
    assert temperatures.transformer == pytest.approx(42.1)


async def test_faults_healthy(inverter: EnertechInverter) -> None:
    await inverter.async_update()
    assert inverter.faults.monitor is MonitorFault.NO_ERROR
    assert inverter.faults.healthy is True


async def test_faults_decode_per_stage(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """Each fault register has its own code space, including its "no error"."""
    mock_modbus_unit.holding[0x15D] = 409  # inverter: output overload trip
    mock_modbus_unit.holding[0x15E] = 313  # battery: high temperature
    await inverter.async_update()
    assert inverter.faults.inverter is InverterFault.OUTPUT_OVERLOAD_TRIP
    assert inverter.faults.battery is BatteryFault.BATTERY_HIGH_TEMPERATURE
    assert inverter.faults.healthy is False


async def test_unknown_fault_code_decodes_to_none(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.holding[0x159] = 599  # not a MonitorFault code
    await inverter.async_update()
    assert inverter.faults.monitor is None


async def test_control_reads_on_demand(inverter: EnertechInverter) -> None:
    """control is not in the poll group; it only has values once asked."""
    await inverter.async_update()
    assert inverter.control.generator_current_limit is None

    await inverter.control.async_update()
    control = inverter.control
    assert control.generator_current_limit == 63
    assert control.generator_run_time == 120
    assert control.generator_start_voltage == 48
    assert control.mode is InverterMode.EXPORT
    # Command word 0x49 -> bits 0, 3 and 6.
    assert control.force_generator_start_stop is True
    assert control.generator_start_auto_manual is False
    assert control.inverter_start_stop is True
    assert control.mppt1_on_off is True
    assert control.mppt2_on_off is False
    assert control.spare_3 is False
