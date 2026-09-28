# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import numpy as np
from jpype import JClass

# JAVA orekit/hipparchus imports
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")
FramesFactory = JClass("org.orekit.frames.FramesFactory")
IERSConventions = JClass("org.orekit.utils.IERSConventions")


class Subsystem:
    """
    The Subsystem class is the base class for all subsystem classes and
    provides generic subsystem functionality
    """

    def __init__(self, name: str, cubesat, mass: float = 0.0, power: float = 0.0, data_generation_rate: float = 0.0):
        """
        Constructor for the Subsystem class.
        :param name:
        :param cubesat:
        :param mass:
        :param power:
        :param data_generation_rate:
        """
        self.name: str = name
        self.cubesat = cubesat
        self.mass: float = mass
        self.power: float = power
        self.data_generation_rate: float = data_generation_rate
        self.ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

    def update(self, dt: float, state):
        """
        Update method for the subsystem ot update the model properties, called at each timestep of the simulation.
        Must be overridden by subsystem-specific implementation
        :param dt: the duration of the timestep
        :param state: the state of the propagation
        :return:
        """
        pass

    def get_power_draw(self) -> float:
        """
        Method to return the current power draw of the subsystem.  By default, it returns the
        static self.power value, but can be overridden by subsystem-specific implementation
        :return:
        """
        return self.power

    def get_mass(self) -> float:
        """
        Method to return the total mass of the subsystem.  By default, it returns the
        static self.mass value, but can be overridden by subsystem-specific implementation
        :return:
        """
        return self.mass

    def get_data_generation_rate(self) -> float:
        """
        Method to return the data generation rate of the subsystem.  By default, it returns the
        static self.data_generation_rate value, but can be overridden by subsystem-specific implementation
        :return:
        """
        return self.data_generation_rate
