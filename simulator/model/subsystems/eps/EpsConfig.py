# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class EpsConfigType(str, Enum):
    SOLAR_PANEL_AREA = "Solar Panel Area (m^2)"
    BATT_CAP = "Battery Capacity (Wh)"
    EPS_MASS = "Mass (kg)"
    EPS_POWER = "Power (W)"
    EPS_DATA_GENERATION_RATE = "Data Generation Rate (bps)"
    INITIAL_SOC = "Initial State of Charge Fraction"


class EpsDataType(Enum):
    BATTERY_SOC = "Battery SOC"
    MAIN_BUS_V = "Main Bus Voltage"
    PANEL_W = "Panel Power"
