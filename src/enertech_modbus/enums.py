"""Coded values the inverter reports, one ``IntEnum`` per code map.

Every map here is transcribed from the corresponding entity declaration in the
``homeassistant-solax-modbus`` Enertech plugin. The fault registers each carry
their own numbering space and each reserves its lowest code for "no error".
"""

from __future__ import annotations

from enum import IntEnum


class ProductType(IntEnum):
    """Register 0x108 — what kind of unit this is."""

    UPS = 1
    RESERVED = 2
    SOLAR_POWER_UNIT = 3
    UPC = 4
    OTHER = 9


class Configuration(IntEnum):
    """Register 0x109 — input/output phase wiring and standalone vs parallel."""

    PHASE1_IN_PHASE1_OUT_STANDALONE = 1
    PHASE1_IN_PHASE3_OUT_STANDALONE = 2
    PHASE3_IN_PHASE3_OUT_STANDALONE = 3
    PHASE3_IN_PHASE1_OUT_STANDALONE = 4
    PHASE1_IN_PHASE1_OUT_PARALLEL = 5
    PHASE1_IN_PHASE3_OUT_PARALLEL = 6
    PHASE3_IN_PHASE3_OUT_PARALLEL = 7
    PHASE3_IN_PHASE1_OUT_PARALLEL = 8
    AC_PHASE1_OUT = 9
    AC_PHASE3_OUT = 10
    DC_OUT = 11
    PHASE3_VARIABLE_FREQUENCY_OUT = 12


class MPPTMode(IntEnum):
    """Register 0x10E — how the MPP tracker is driven."""

    AUTO = 1
    SHORT = 2
    MANUAL = 3


class InverterMode(IntEnum):
    """The operating mode: reported at 0x10F, set at 0x1A5.

    The plugin declares the two registers with separately written labels that
    differ only cosmetically (0x10F "Back Mode" vs 0x1A5 "Backup Mode"); the
    codes are identical, so one enum covers both.
    """

    SAVING = 1
    BACKUP = 2
    EXPORT = 3
    BATTERY_LESS = 4
    REMOTE_CONTROL = 5


class MonitorFault(IntEnum):
    """Register 0x159 — supervisory faults."""

    NO_ERROR = 500
    CAN_BUS_ERROR = 501
    BATTERY_BMS_COM_ERROR = 502
    BATTERY_RELAY_OPEN = 503
    SMOKE_DETECTED = 504
    OUTPUT_MCB_TRIP = 505
    EARTH_LEAKAGE = 506
    DIESEL_GENERATOR_ON = 507
    REMOTE_SHUTDOWN = 508
    ENERGY_METER_COM_ERROR = 509


class GridFault(IntEnum):
    """Register 0x15A — grid/input side faults."""

    NO_ERROR = 100
    INPUT_LOW_VOLTAGE = 101
    INPUT_HIGH_VOLTAGE = 102
    INPUT_LOW_FREQUENCY = 103
    INPUT_HIGH_FREQUENCY = 104
    INPUT_SEQUENCE_ERROR = 105
    INPUT_OVERLOAD = 106
    INPUT_CURRENT_UNBALANCE = 107
    INPUT_VOLTAGE_UNBALANCE = 108


class PFCFault(IntEnum):
    """Register 0x15B — PFC rectifier faults."""

    NO_ERROR = 600
    PFC_IGBT_ERROR = 601
    INPUT_DC_LOW = 602
    INPUT_DC_HIGH = 603
    OUTPUT_DC_HIGH = 604
    OUTPUT_DC_LOW = 605
    PFC_TOTAL_CURRENT_LIMIT = 606
    PFC_BATTERY_CURRENT_LIMIT = 607
    POSITIVE_BUS_UNDER = 608
    NEGATIVE_BUS_UNDER = 609
    POSITIVE_BUS_OVER = 610
    NEGATIVE_BUS_OVER = 611
    DC_BUS_UNBALANCE = 612
    PFC_MODULE_OVERTEMPERATURE = 613
    DC_BUS_SOFT_START_FAIL = 614
    CHARGER_SOFT_START_FAILURE = 615


class SolarFault(IntEnum):
    """Register 0x15C — solar string 1 faults.

    Numerically overlaps :class:`PFCFault` but is a separate code space.
    """

    NO_ERROR = 600
    SOLAR1_EXTERNAL_OFF = 601
    SOLAR1_IGBT_ERROR = 602
    OUTPUT_DC_HIGH = 603
    SOLAR1_INPUT_VOLTAGE_LOW = 604
    SOLAR1_INPUT_VOLTAGE_HIGH = 605
    SOLAR1_POWER_LIMIT = 606
    OUTPUT_DC_LOW = 607


class InverterFault(IntEnum):
    """Register 0x15D — inverter-stage faults."""

    NO_ERROR = 400
    INVERTER_IGBT_FAULT = 401
    USER_STOP = 402
    EXTERNAL_EPO_STOP = 403
    OUTPUT_LOW_VOLTAGE = 404
    OUTPUT_HIGH_VOLTAGE = 405
    OUTPUT_FREQUENCY_LOW = 406
    OUTPUT_FREQUENCY_HIGH = 407
    OUTPUT_OVERLOAD_ALARM = 408
    OUTPUT_OVERLOAD_TRIP = 409
    INVERTER_MODULE_HIGH_TEMPERATURE = 410
    LOAD_TRANSFER_TO_BYPASS = 411
    LOAD_RETRANSFER_FROM_BYPASS = 412
    OUTPUT_VOLTAGE_UNBALANCE = 413
    OUTPUT_CURRENT_UNBALANCE = 414
    REGENERATIVE_TRANSFER = 415
    TERMINAL_VOLT_ERROR = 416
    SPD_FAIL = 417
    GRID_NOT_IN_SYNC = 418


class BatteryFault(IntEnum):
    """Register 0x15E — battery-stage faults.

    Several codes report a normal condition (equalize charging, test in
    progress) rather than a failure; they are reported as the device sends them.
    """

    NO_ERROR = 300
    BATTERY_IGBT_FAULT = 301
    BATTERY_LOW_VOLTAGE = 302
    BATTERY_HIGH_VOLTAGE = 303
    BATTERY_LOW_WARNING = 304
    BATTERY_EARTH_FAULT = 305
    BATTERY_TEMP_COMPENSATION = 306
    BATTERY_EQUALIZE_CHARGING = 307
    BATTERY_TEST_PROGRESS = 308
    BATTERY_TEST_FAIL = 309
    BATTERY_OVER_CURRENT_CHARGE = 310
    BATTERY_OVER_CURRENT_DISCHARGE = 311
    BATTERY_MODULE_OVERTEMPERATURE = 312
    BATTERY_HIGH_TEMPERATURE = 313
    BATTERY_LOW_TEMPERATURE = 314
    BATTERY_COM_ERROR = 315
