# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class AdcsConfigType(str, Enum):
    ADCS_MASS = "Mass (kg)"
    ADCS_POWER = "Power (W)"
    ADCS_DATA_GENERATION_RATE = "Data Generation Rate (bps)"
    WHEEL_INERTIA = "Reaction Wheel Inertia"
    MAX_WHEEL_SPEED = "Max Reaction Wheel Speed"
    MAX_WHEEL_ACCEL = "Max Reaction Wheel Acceleration"
    WHEEL_EFFICIENCY = "Reaction Wheel efficiency"
    WHEEL_IDLE_POWER_COEFF = "Reaction Wheel Idle Power Coefficient"


class AdcsDataType(Enum):
    ROLL = "Roll"
    PITCH = "Pitch"
    YAW = "Yaw"
    WHEEL_SPEED_1 = "Wheel 1 Angular Velocity"
    WHEEL_SPEED_2 = "Wheel 2 Angular Velocity"
    WHEEL_SPEED_3 = "Wheel 3 Angular Velocity"
    WHEEL_SPEED_4 = "Wheel 4 Angular Velocity"
