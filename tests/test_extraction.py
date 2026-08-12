"""Guards that the extraction from the upstream plugin stayed complete.

The addresses below are every register the Enertech plugin of
homeassistant-solax-modbus declares — 54 sensors, 3 numbers, 1 select and 16
switch bits sharing one command word — transcribed from its entity lists. If a
field is dropped or moved, this fails.
"""

from __future__ import annotations

from enertech_modbus import EnertechInverter

# Sensor entities: address -> registers it spans.
SENSOR_REGISTERS = {
    0x108: 1, 0x109: 1, 0x10E: 1, 0x10F: 1,
    0x111: 1, 0x112: 1, 0x113: 1, 0x114: 1, 0x115: 1, 0x116: 1,
    0x119: 1, 0x11A: 1, 0x11B: 1, 0x11C: 1, 0x11D: 1, 0x11E: 1, 0x11F: 1,
    0x120: 1, 0x124: 1, 0x125: 1, 0x126: 1, 0x127: 1, 0x128: 1, 0x129: 1,
    0x12A: 1, 0x12D: 1, 0x12E: 1, 0x12F: 1,
    0x130: 1, 0x133: 1, 0x134: 1, 0x135: 1, 0x136: 1,
    0x13B: 1, 0x13C: 1, 0x13D: 1, 0x13E: 1, 0x142: 1,
    0x146: 2,  # uint32
    0x152: 2, 0x154: 2,  # float32
    0x159: 1, 0x15A: 1, 0x15B: 1, 0x15C: 1, 0x15D: 1, 0x15E: 1,
    0x15F: 1, 0x160: 1, 0x161: 1, 0x162: 1, 0x169: 1,
    0x222: 1, 0x224: 1,
}  # fmt: skip

# Number, select and switch entities.
CONTROL_REGISTERS = {0x196, 0x197, 0x198, 0x199, 0x1A5}

COMMAND_BITS = 16  # switch entities, all on 0x196


def test_every_sensor_register_is_modelled(inverter: EnertechInverter) -> None:
    modelled = {
        resolved.address: resolved.count
        for component in (*inverter.polled_components, inverter.identity)
        for resolved in component.resolved_fields.values()
    }
    modelled.pop(0x14)  # the serial number, read by a helper rather than an entity

    assert modelled == SENSOR_REGISTERS
    assert len(SENSOR_REGISTERS) == 54


def test_every_control_register_is_modelled(inverter: EnertechInverter) -> None:
    fields = inverter.control.resolved_fields
    assert {resolved.address for resolved in fields.values()} == CONTROL_REGISTERS

    command_bits = [name for name, r in fields.items() if r.address == 0x196]
    assert len(command_bits) == COMMAND_BITS
    assert len(fields) == COMMAND_BITS + 4  # + three settings and the mode select


def test_every_field_is_writable_only_where_the_plugin_writes(
    inverter: EnertechInverter,
) -> None:
    """Sensors are read-only; the numbers, the select and the bits are writable."""
    for component in (*inverter.polled_components, inverter.identity):
        for name, resolved in component.resolved_fields.items():
            assert not resolved.field.writable, name

    for name, resolved in inverter.control.resolved_fields.items():
        assert resolved.field.writable, name
