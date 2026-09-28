# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class StructureConfigType(str, Enum):
    DRAG_AREA = "Drag Cross Sectional Area (m^2)"
    DRAG_COEF = "Coefficient of Drag"
    STRUCTURE_MASS = "Mass (kg)"
    I_XX = "Principle Moment of Inertia xx"
    I_YY = "Principle Moment of Inertia yy"
    I_ZZ = "Principle Moment of Inertia zz"
    MODEL_FILE_3D = "3D Model file (e.g. .ply)"


class StructureDataType(Enum):
    TEMPERATURE = "Temperature"
