"""The top-level Enertech device object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modbus_connection.model import Component, ComponentGroup

from .battery import Battery
from .control import Control
from .energy import Energy
from .faults import Faults
from .grid import Grid
from .identity import Identity
from .inverter import Inverter
from .output import Output
from .solar import Solar
from .status import Status
from .temperatures import Temperatures

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit


class EnertechInverter:
    """An Enertech Solar inverter reached through a ``ModbusUnit``.

    The device is a tree of independently-updatable sub-systems::

        inverter = EnertechInverter(unit)
        await inverter.async_update()
        inverter.battery.capacity      # %
        inverter.solar.voltage_1       # V
        inverter.faults.inverter       # InverterFault | None
        inverter.identity.serial_number

    :attr:`identity` cannot change while the unit runs, so :meth:`async_setup`
    reads it once and a poll leaves it alone. :attr:`control` holds the writable
    settings and the command word; the plugin this map comes from never reads
    those registers back, so a poll does not either — refresh it yourself with
    ``await inverter.control.async_update()`` before trusting its values.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self.identity = Identity(unit)
        self.status = Status(unit)
        self.grid = Grid(unit)
        self.inverter = Inverter(unit)
        self.output = Output(unit)
        self.battery = Battery(unit)
        self.solar = Solar(unit)
        self.energy = Energy(unit)
        self.temperatures = Temperatures(unit)
        self.faults = Faults(unit)
        self.control = Control(unit)
        self._group: ComponentGroup | None = None

    @property
    def polled_components(self) -> tuple[Component, ...]:
        """The sub-systems a poll refreshes."""
        return (
            self.status,
            self.grid,
            self.inverter,
            self.output,
            self.battery,
            self.solar,
            self.energy,
            self.temperatures,
            self.faults,
        )

    async def async_setup(self) -> None:
        """Read what cannot change while the unit runs, and build the poll group."""
        await self.identity.async_update()
        self._group = ComponentGroup(self._unit, self.polled_components)

    async def async_update(self) -> None:
        """Refresh every polled sub-system in one pooled set of block reads.

        The first call sets the device up. A failure leaves it unset up, so the
        next call tries again.
        """
        if self._group is None:
            await self.async_setup()
        assert self._group is not None  # async_setup() always builds it
        await self._group.async_update()
