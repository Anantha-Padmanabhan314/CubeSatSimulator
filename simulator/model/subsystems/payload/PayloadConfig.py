# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class PayloadConfigType(str, Enum):
    TETHER_BARE_LEN = "Tether Bare Length (m)"
    TETHER_INSULATED_LEN = "Tether Insulated Length (m)"
    TETHER_CONDUCTIVITY = "Tether Conductivity (S/m)"
    TETHER_CROSS_SECTION_AREA = "Tether Cross-Section Area (m^2)"
    TETHER_PERIMETER = "Tether Perimeter (m)"
    TETHER_AEE_POTENTIAL = "AEE Potential Drop (V)"
    PAYLOAD_MASS = "Mass (kg)"
    PAYLOAD_POWER = "Power (W)"
    PAYLOAD_DATA_GENERATION_RATE = "Data Generation Rate (bps)"


class PayloadDataType(Enum):
    TETHER_FORCE = "Tether Force"
    TETHER_CURRENT = "Tether Current (A)"
