# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from simulator.model.DataStore import SpacecraftDataType
from simulator.model.subsystems.structure.StructureConfig import StructureConfigType
from simulator.model.subsystems.Subsystem import Subsystem


class StructureSubsystem(Subsystem):
    """
    The Structure Subsystem class.
    """
    def __init__(self, cubesat, structure_config):
        """
        Constructor for the structure subsystem
        :param cubesat:
        :param structure_config:
        """
        super().__init__("Structure", cubesat, structure_config[StructureConfigType.STRUCTURE_MASS], 0)
        self.drag_area = structure_config[StructureConfigType.DRAG_AREA]
        self.drag_coef = structure_config[StructureConfigType.DRAG_COEF]
        self.Ixx = structure_config[StructureConfigType.I_XX]
        self.Iyy = structure_config[StructureConfigType.I_YY]
        self.Izz = structure_config[StructureConfigType.I_ZZ]

    def update(self, dt: float, state) -> None:
        """
        Update method for the structure subsystem - currently only records attitude information.
        :param dt: the duration of the timestep
        :param state: the state of the propagation
        :return:
        """
        self.cubesat.data_store.spacecraft_data[SpacecraftDataType.Q_ECI].append(self.cubesat.q_body_eci)
        self.cubesat.data_store.spacecraft_data[SpacecraftDataType.RPY_ECI].append(self.cubesat.rpy_body_eci)
        self.cubesat.data_store.spacecraft_data[SpacecraftDataType.Q_LVLH].append(self.cubesat.q_body_lvlh)
        self.cubesat.data_store.spacecraft_data[SpacecraftDataType.RPY_LVLH].append(self.cubesat.rpy_body_lvlh)
        pass
