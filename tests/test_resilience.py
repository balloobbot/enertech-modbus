"""One failing block must not take the rest of the poll with it.

The integration reads its blocks independently and tolerates a failure
(``auto_block_ignore_readerror=True``): the failing block's sensors keep their
last values while everything else refreshes. The library mirrors that at
sub-system granularity.
"""

from __future__ import annotations

import pytest
from modbus_connection import ModbusConnectionError, ModbusTimeoutError
from modbus_connection.mock import MockModbusUnit

from enertech_modbus import EnertechInverter, InverterMode


async def test_a_failed_component_leaves_the_rest_fresh(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await inverter.async_update()
    before = inverter.grid.voltage_r

    mock_modbus_unit.holding[0x111] = 251  # grid voltage changes on the device
    mock_modbus_unit.holding[0x133] = 61  # so does the battery's state of charge
    mock_modbus_unit.fail_read(0x111, ModbusTimeoutError("slow grid block"))
    report = await inverter.async_update()

    assert not report.complete
    assert set(report.failed) == {"grid"}
    assert isinstance(report.failed["grid"], ModbusTimeoutError)
    assert "battery" in report.updated
    assert inverter.grid.voltage_r == before
    assert inverter.battery.capacity == 61


async def test_listeners_fire_at_the_end_and_only_for_fresh_components(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await inverter.async_update()
    seen: list[int] = []
    inverter.battery.add_update_listener(
        lambda: seen.append(len(mock_modbus_unit.read_events))
    )
    inverter.grid.add_update_listener(lambda: seen.append(-1))

    mock_modbus_unit.fail_read(0x111, ModbusTimeoutError("slow grid block"))
    mock_modbus_unit.read_events.clear()
    await inverter.async_update()

    # One notification, after every sub-system was tried; none for the failure.
    assert seen == [len(mock_modbus_unit.read_events)]


async def test_a_dead_link_raises_instead_of_reporting(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await inverter.async_update()
    mock_modbus_unit.fail_requests(ModbusConnectionError("link down"))
    with pytest.raises(ModbusConnectionError):
        await inverter.async_update()


async def test_every_component_refreshes_on_a_healthy_device(
    inverter: EnertechInverter,
) -> None:
    report = await inverter.async_update()

    assert report.complete
    assert report.failed == {}
    assert report.updated == {
        "status",
        "grid",
        "inverter",
        "output",
        "battery",
        "solar",
        "energy",
        "temperatures",
        "faults",
    }
    assert "control" not in report.updated  # write-oriented, never polled
    assert "identity" not in report.updated  # setup read it


async def test_a_two_block_component_fails_whole(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """status is planned as two far-apart blocks but still updates atomically.

    Its second block carries the run-time counters; failing it must not leave the
    modes from the first block refreshed while the counters go stale, because a
    consumer reading both would see two different moments.
    """
    await inverter.async_update()

    mock_modbus_unit.holding[0x10F] = 1  # mode -> something other than EXPORT
    mock_modbus_unit.holding[0x15F] = 9999
    mock_modbus_unit.fail_read(0x15F, ModbusTimeoutError("slow counters"))
    report = await inverter.async_update()

    assert set(report.failed) == {"status"}
    assert inverter.status.mode is InverterMode.EXPORT  # the first block, unapplied
    assert inverter.status.inverter_run_time == 1234


async def test_a_failed_identity_read_does_not_hold_the_poll_back(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """Nothing in the poll depends on identity, so it must not gate setup."""
    mock_modbus_unit.fail_read(0x14, ModbusTimeoutError("no serial"))
    report = await inverter.async_update()

    assert set(report.failed) == {"identity"}
    assert inverter.identity.serial_number is None
    assert inverter.battery.capacity == 87  # the rest of the device still read


async def test_identity_is_retried_until_it_reads_then_dropped(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """A transient identity failure must not latch a permanent "unknown"."""
    mock_modbus_unit.fail_read(0x14, ModbusTimeoutError("no serial"))
    await inverter.async_update()

    mock_modbus_unit.fail_read(0x14, None)  # the device answers again
    report = await inverter.async_update()
    assert report.complete
    assert "identity" in report.updated
    assert inverter.identity.serial_number == "ENT12345"

    # Read once, then never again: identity leaves the poll list.
    mock_modbus_unit.read_events.clear()
    report = await inverter.async_update()
    assert "identity" not in report.updated
    assert not any(event.address == 0x14 for event in mock_modbus_unit.read_events)


async def test_a_dead_link_during_setup_raises_and_retries(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """The link failing leaves the device unset up rather than half set up."""
    mock_modbus_unit.fail_requests(ModbusConnectionError("link down"))
    with pytest.raises(ModbusConnectionError):
        await inverter.async_update()

    mock_modbus_unit.fail_requests(None)
    report = await inverter.async_update()
    assert report.complete
    assert inverter.identity.serial_number == "ENT12345"
