"""The top-level Enertech device object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modbus_connection import ModbusConnectionError, ModbusError

from .battery import Battery
from .control import Control
from .energy import Energy
from .faults import Faults
from .grid import Grid
from .identity import Identity
from .inverter import Inverter
from .model import EnertechComponent, UpdateReport
from .output import Output
from .solar import Solar
from .status import Status
from .temperatures import Temperatures

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

# Every component attribute a poll refreshes, in read order. identity is absent:
# setup reads it once. control is absent because the plugin never reads it back.
_POLLED = (
    "status",
    "grid",
    "inverter",
    "output",
    "battery",
    "solar",
    "energy",
    "temperatures",
    "faults",
)


class EnertechInverter:
    """An Enertech Solar inverter reached through a ``ModbusUnit``.

    The device is a tree of independently-updatable sub-systems::

        inverter = EnertechInverter(unit)
        await inverter.async_update()
        inverter.battery.capacity      # %
        inverter.solar.voltage_1       # V
        inverter.faults.inverter       # InverterFault | None
        inverter.identity.serial_number

    A poll reads each sub-system on its own and reports what it refreshed, so one
    slow or refused block costs that sub-system's values and nothing else.

    :attr:`identity` cannot change while the unit runs, so :meth:`async_setup`
    reads it once and a poll leaves it alone. :attr:`control` holds the writable
    settings and the command word; the plugin this map comes from never reads
    those registers back, so a poll does not either — refresh it yourself with
    ``await inverter.control.async_update()`` before trusting its values.
    """

    def __init__(self, unit: ModbusUnit) -> None:
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
        self._polled: list[str] | None = None

    async def async_setup(self) -> None:
        """Read what cannot change while the unit runs, and settle the poll list.

        A failure leaves the device unset up, so the next update tries again.
        """
        await self.identity.async_update()
        self._polled = list(_POLLED)

    async def async_update(self) -> UpdateReport:
        """Refresh every polled sub-system, one at a time.

        The first call sets the device up. Sub-systems are read independently,
        the way the plugin reads its blocks: one whose read fails keeps its
        previous values while the rest still refresh. Listeners fire only after
        every sub-system has been tried, and only on the ones that refreshed. A
        failure of the link itself raises ``ModbusConnectionError`` instead of
        reporting.
        """
        if self._polled is None:
            await self.async_setup()
        assert self._polled is not None  # async_setup() always builds it
        updated: set[str] = set()
        failed: dict[str, ModbusError] = {}
        for name in self._polled:
            component: EnertechComponent = getattr(self, name)
            try:
                await component.async_update(notify=False)
            except ModbusConnectionError:
                raise
            except ModbusError as err:
                failed[name] = err
            else:
                updated.add(name)
        for name in updated:
            fresh: EnertechComponent = getattr(self, name)
            fresh.notify()
        return UpdateReport(updated, failed)
