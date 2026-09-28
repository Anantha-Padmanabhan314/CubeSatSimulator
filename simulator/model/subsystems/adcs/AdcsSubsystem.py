# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from simulator.model.subsystems.adcs.AdcsConfig import AdcsConfigType
from simulator.model.subsystems.Subsystem import Subsystem


class AdcsSubsystem(Subsystem):
    """
    Attitude Determination and Control System.
    """
    def __init__(self, cubesat, adcs_config):
        """
        ADCS Subsystem constructore
        :param cubesat: the parent cubesat
        :param adcs_config: the ADCS configuration data
        """
        super().__init__("ADCS", cubesat,
                         adcs_config[AdcsConfigType.ADCS_MASS],
                         adcs_config[AdcsConfigType.ADCS_POWER],
                         adcs_config[AdcsConfigType.ADCS_DATA_GENERATION_RATE])
        self.torque = [0,0,0]

    def update(self, dt: float, state) -> None:
        """
        Update method for the ADCS subsystem.  In the future may include a PID controller for calculating torques
        to manage target attitudes and slews.
        :param dt: the duration of the timestep
        :param state: the state of the propagation
        :return:
        """
        pass
