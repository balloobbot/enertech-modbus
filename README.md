# enertech-modbus

A standalone Python library that reads an **Enertech Solar** hybrid inverter over
Modbus, exposed as a normal, object-oriented Python API.

The register map — addresses, scales, data types and code maps — is based on the
Enertech plugin of the
[homeassistant-solax-modbus](https://github.com/wills106/homeassistant-solax-modbus)
integration (Apache-2.0), and is verified in tests against an in-memory mock of
the inverter.

## Design

- It **takes a `ModbusUnit`**, not a connection and not a host and port. You own
  the connection and choose the backend (tmodbus, pymodbus, …); this library only
  reads and writes registers.
- **ASCII-over-TCP is not supported.** The library exposes no connect helper and
  will not work correctly behind an ASCII-framed TCP link; use RTU or RTU-over-TCP.
- Everything lives in the **holding-register space** (FC03). The device has no
  coils and no input registers; the only booleans are the sixteen bits packed
  into command word 0x196.
- The inverter is a tree of independently-updatable sub-systems, each a
  `Component` that knows its own registers:

  | Attribute | What |
  | --- | --- |
  | `identity` | serial number, product type, phase configuration |
  | `status` | operating mode, MPPT mode, lifetime run-time counters |
  | `grid` | grid voltages, currents, frequency, power factor |
  | `inverter` | inverter-stage voltages, currents, frequency |
  | `output` | output voltages, load currents, frequency, power factor, load % |
  | `battery` | voltage, state of charge, currents, PV charge current |
  | `solar` | PV string voltages and currents, string 2 power, string 1 energy |
  | `energy` | lifetime grid import and export totals |
  | `temperatures` | DC-DC, DC-AC and transformer temperatures |
  | `faults` | the current fault code of each of the six stages |
  | `control` | writable generator settings, mode setting, command bits |

- **Set up once, then poll.** `identity` cannot change while the unit runs, so
  `async_setup()` reads it once (2 reads); `async_update()` then refreshes the
  nine polled sub-systems in **8 block reads totalling 70 registers**, pooled
  across sub-systems wherever their blocks meet.
- `control` is **not polled**. The upstream plugin declares those registers as
  write-only entities and never reads them back, so neither does a poll here —
  call `await inverter.control.async_update()` yourself first if you want to read
  the current settings.

## Supported devices

The upstream plugin declares a single variant. It has the generation and
variant bit flags (`GEN`/`GEN2`/`GEN3`/`GEN4`, `X1`/`X3`, `EPS`, `DCB`, `PM`)
that the other plugins of that integration use, but **every** Enertech entity is
declared with the empty mask, so every register applies to every unit and there
is nothing to filter. This library therefore models one device with no variants.

The plugin's own type detection only ever resolves to the base generation, and
the register map is written for a three-phase (R/Y/B) hybrid inverter with two
PV strings, a battery bank and a diesel generator input. A single-phase unit
reports only the R phase.

## Use

```python
import asyncio

from modbus_connection import ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from enertech_modbus import EnertechInverter, InverterMode


async def main() -> None:
    connection = ModbusConnection(
        ModbusTcpParams(host="192.168.1.50", port=502, framer="rtu")
    )
    try:
        inverter = EnertechInverter(connection.for_unit(1))
        await inverter.async_update()

        print("Serial:", inverter.identity.serial_number)
        print("Mode:", inverter.status.mode)
        print("Battery:", inverter.battery.capacity, "%")
        print("PV 1:", inverter.solar.voltage_1, "V", inverter.solar.current_1, "A")
        print("Grid import:", inverter.energy.grid_import, "kWh")
        if not inverter.faults.healthy:
            print("Faults:", inverter.faults.inverter, inverter.faults.battery)

        await inverter.control.set_mode(InverterMode.EXPORT)
    finally:
        await connection.close()


asyncio.run(main())
```

## Caveats

- The sixteen command bits of 0x196 are transcribed from the plugin's switch
  entities, which carry **no write function upstream** and so never reach a real
  device. Their addresses and bit positions are as declared, but the write
  semantics are untested: this library writes a bit as a read-modify-write of
  0x196, which suits a latching control word and not a device expecting a pulse.
- `solar.energy_1` is declared upstream under a name that says power but with
  energy units and a total-increasing state class; it is modelled as energy.

## Licence

Apache-2.0, inherited from
[homeassistant-solax-modbus](https://github.com/wills106/homeassistant-solax-modbus).
