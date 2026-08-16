#!/usr/bin/env python3

"""Query an Enertech Solar inverter and print every value.

Reads one inverter once and dumps it to the terminal — the quickest way to check
real hardware with no application around it.

``control`` is left out for the same reason no poll reads it: those registers
are write-only upstream, so a unit that refuses them would cost the whole dump.

::

    uv run script/query.py /dev/ttyUSB0 --transport serial --unit 1
    uv run script/query.py 192.168.1.50 --unit 1
"""

from __future__ import annotations

import argparse
import asyncio

from modbus_connection import ModbusError
from modbus_connection.cli_helper import (
    CountingUnit,
    add_connection_args,
    connect_from_args,
    print_component,
)

from enertech_modbus import EnertechInverter

# The inverter is RS-485 RTU, reached either through a transparent TCP gateway
# or directly. Neither ASCII nor native Modbus TCP framing is supported. tcp
# leads: it is the default transport.
CONNECTIONS = (("tcp", "rtu"), ("serial", "rtu"))


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser, connections=CONNECTIONS)
    parser.add_argument("--unit", type=int, default=1, help="Modbus unit id")
    args = parser.parse_args()

    try:
        connection = await connect_from_args(args)
    except ModbusError as err:
        print(f"Could not connect: {err}")
        return 1

    counting = CountingUnit(connection.for_unit(args.unit))
    inverter = EnertechInverter(counting)
    try:
        report = await inverter.async_update()
    except ModbusError as err:
        print(f"Could not read the inverter: {err}")
        return 1
    finally:
        await connection.close()

    # A failed sub-system still prints, holding its previous values — say so,
    # or its empty values read as the inverter's answer.
    for name, error in report.failed.items():
        print(f"{name} was not read: {error}")

    print_component(inverter.identity, title="Identity")
    print_component(inverter.status, title="Status")
    print_component(inverter.grid, title="Grid")
    print_component(inverter.inverter, title="Inverter")
    print_component(inverter.output, title="Output")
    print_component(inverter.battery, title="Battery")
    print_component(inverter.solar, title="Solar")
    print_component(inverter.energy, title="Energy")
    print_component(inverter.temperatures, title="Temperatures")
    print_component(inverter.faults, title="Faults")
    print(f"\n{counting.reads} Modbus reads")
    return 0


raise SystemExit(asyncio.run(main()))
