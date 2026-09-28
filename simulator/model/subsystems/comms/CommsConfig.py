# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class CommsConfigType(str, Enum):
    TX_DATARATE = "Transmit Datarate (bps)"
    DATA_STORAGE_CAPACITY = "Data Storage Capacity (bits)"
    COMMS_MASS = "Mass (kg)"
    COMMS_POWER = "Power (W) (not-transmitting)"
    COMMS_TX_POWER = "Power (W) (transmitting)"

class CommsDataType(Enum):
    DATA_STORAGE = "Data Storage"
