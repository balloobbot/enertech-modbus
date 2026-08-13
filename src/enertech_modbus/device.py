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
# setup reads it once, and it only joins the list while that read is outstanding.
# control is absent because the plugin this map comes from never reads it back.
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

        The poll does not need identity — no register map here depends on it — so
        a refused or timed-out identity read does not hold the device back: it
        joins the poll list instead and is retried until it reads. Only the link
        itself failing leaves the device unset up, for the next call to try again.
        """
        polled = list(_POLLED)
        try:
            await self.identity.async_update()
        except ModbusConnectionError:
            raise
        except ModbusError:
            polled.insert(0, "identity")
        self._polled = polled

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
        if "identity" in updated:
            self._polled.remove("identity")  # static: read once, then never again
        return UpdateReport(updated, failed)

    async def async_read_raw(self) -> dict[str, dict[int, int | bool]]:
        """Every register this device reads, undecoded — for diagnostics.

        The identity registers come along: setup reads them once and a poll
        leaves them alone, and they are the first thing an issue report is read
        for. :attr:`control` stays out — nothing here ever reads those
        registers, so a device that serves them for writing alone would fail the
        whole dump; read it yourself with ``await inverter.control.async_read_raw()``
        if you want them anyway. The first call sets the device up. A block the
        device refuses raises, since there the error is the point.
        """
        if self._polled is None:
            await self.async_setup()
        assert self._polled is not None  # async_setup() always builds it
        raw: dict[str, dict[int, int | bool]] = {}
        for name in dict.fromkeys(("identity", *self._polled)):  # identity may be both
            component: EnertechComponent = getattr(self, name)
            for space, values in (await component.async_read_raw()).items():
                raw.setdefault(space, {}).update(values)
        return {space: dict(sorted(values.items())) for space, values in raw.items()}
