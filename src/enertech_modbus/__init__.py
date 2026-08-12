"""enertech-modbus — read an Enertech Solar inverter over Modbus.

Construct ``EnertechInverter(unit)`` with a ``modbus_connection.ModbusUnit``,
call ``await device.async_update()``, then read its sub-systems as normal Python
objects::

    device.grid.voltage_r
    device.battery.capacity
    device.solar.energy_1
    device.faults.inverter

The register map is transcribed from the Enertech plugin of the
`homeassistant-solax-modbus <https://github.com/wills106/homeassistant-solax-modbus>`_
integration. Everything lives in the holding-register space (FC03); the device
has no coils or input registers, and booleans are packed as bits in the command
word 0x196.
"""

from .battery import Battery
from .control import Control
from .device import EnertechInverter
from .energy import Energy
from .enums import (
    BatteryFault,
    Configuration,
    GridFault,
    InverterFault,
    InverterMode,
    MonitorFault,
    MPPTMode,
    PFCFault,
    ProductType,
    SolarFault,
)
from .faults import Faults
from .grid import Grid
from .identity import Identity
from .inverter import Inverter
from .output import Output
from .solar import Solar
from .status import Status
from .temperatures import Temperatures

__all__ = [
    "Battery",
    "BatteryFault",
    "Configuration",
    "Control",
    "Energy",
    "EnertechInverter",
    "Faults",
    "Grid",
    "GridFault",
    "Identity",
    "Inverter",
    "InverterFault",
    "InverterMode",
    "MPPTMode",
    "MonitorFault",
    "Output",
    "PFCFault",
    "ProductType",
    "Solar",
    "SolarFault",
    "Status",
    "Temperatures",
]
