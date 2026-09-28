# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class GroundConfigType(str, Enum):
    STATIONS = "Station List"
    BAND_FILTER = "Band Filter"

class GroundDataType(Enum):
    SAT_NADIR_LAT = "Satellite nadir point latitude"
    SAT_NADIR_LONG = "Satellite nadir point longitude"
    GROUND_VISIBLE = "Ground Visible from CubeSat"

