"""What a poll actually asks the device for.

These pin the block reads the planner issues, and check they are right rather
than merely recording them: every field is covered, no block starts or ends on a
register no field claims, nothing exceeds the 100-register cap the plugin polls
this device with, and a poll never touches the control registers.

No component declares ``register_ranges`` — the plugin declares no block
boundaries of its own, so the blocks below are planned from the fields. Members
of a group merge only where their blocks meet, which is why the run of
sub-systems from 0x111 to 0x136 becomes one read while the three stragglers at
the top of the map stay separate.
"""

from __future__ import annotations

from modbus_connection.mock import MockModbusUnit
from modbus_connection.model import Component

from enertech_modbus import EnertechInverter
from enertech_modbus.model import MAX_READ_SPAN

SETUP_BLOCKS = [(0x14, 4), (0x108, 2)]
POLL_BLOCKS = [
    (0x10E, 2),  # status: MPPT mode, inverter mode
    (0x111, 38),  # grid + inverter + output + battery + DC-DC temperature
    (0x13B, 13),  # solar
    (0x152, 4),  # energy (two float32)
    (0x159, 10),  # faults + the run-time counters that follow them
    (0x169, 1),  # DC-AC temperature
    (0x222, 1),  # transformer temperature
    (0x224, 1),  # battery PV charge current
]


def blocks(unit: MockModbusUnit) -> list[tuple[int, int]]:
    return [(event.address, event.count) for event in unit.read_events]


def covered(unit: MockModbusUnit) -> set[int]:
    """Every holding address the reads so far touched."""
    return {
        address
        for event in unit.read_events
        for address in range(event.address, event.address + event.count)
    }


def claimed(*components: Component) -> set[int]:
    """Every holding address the components' fields sit on."""
    return {
        address
        for component in components
        for resolved in component.resolved_fields.values()
        for address in range(resolved.address, resolved.address + resolved.count)
    }


async def test_setup_reads_identity_in_two_blocks(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """The serial sits far from the type registers, so they cannot share a read."""
    await inverter.async_setup()

    assert blocks(mock_modbus_unit) == SETUP_BLOCKS
    assert claimed(inverter.identity) <= covered(mock_modbus_unit)


async def test_poll_covers_every_polled_field(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    await inverter.async_setup()
    mock_modbus_unit.read_events.clear()
    await inverter.async_update()

    assert blocks(mock_modbus_unit) == POLL_BLOCKS
    assert claimed(*inverter.polled_components) <= covered(mock_modbus_unit)


async def test_poll_blocks_are_well_formed(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """Holding registers only, within the read cap, and no wasted block edges."""
    await inverter.async_update()

    fields = claimed(*inverter.polled_components, inverter.identity)
    for event in mock_modbus_unit.read_events:
        assert event.register_type == "holding"
        assert event.count <= MAX_READ_SPAN
        assert event.address in fields  # a block never starts on a spare register
        assert event.address + event.count - 1 in fields  # nor ends on one


async def test_poll_does_not_touch_the_control_registers(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """control is write-oriented and deliberately left out of the poll group."""
    await inverter.async_update()

    assert not covered(mock_modbus_unit) & claimed(inverter.control)


async def test_first_update_sets_up_then_polls(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """The identity reads happen once; later polls are the poll blocks alone."""
    await inverter.async_update()
    assert blocks(mock_modbus_unit) == SETUP_BLOCKS + POLL_BLOCKS

    mock_modbus_unit.read_events.clear()
    await inverter.async_update()
    assert blocks(mock_modbus_unit) == POLL_BLOCKS


async def test_poll_reads_70_registers(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """The 55 registers the fields claim, plus 15 spare ones bridged by merges."""
    await inverter.async_setup()
    mock_modbus_unit.read_events.clear()
    await inverter.async_update()

    assert len(claimed(*inverter.polled_components)) == 55
    assert sum(event.count for event in mock_modbus_unit.read_events) == 70


async def test_control_reads_one_block(
    inverter: EnertechInverter, mock_modbus_unit: MockModbusUnit
) -> None:
    """The command word, the three settings and the mode select share a read."""
    await inverter.control.async_update()

    assert blocks(mock_modbus_unit) == [(0x196, 16)]  # 0x196-0x1A5 inclusive
    assert claimed(inverter.control) <= covered(mock_modbus_unit)


async def test_no_bit_space_is_used(inverter: EnertechInverter) -> None:
    """The device has no coils or discrete inputs; 0x196's bits are packed."""
    for component in (*inverter.polled_components, inverter.identity, inverter.control):
        assert component.register_space == "holding"
        assert component.coil_ranges is None
        assert component.discrete_ranges is None
        assert component.register_ranges is None
