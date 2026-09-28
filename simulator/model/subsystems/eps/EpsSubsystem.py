# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math
import numpy as np

from simulator.model.subsystems.eps.Battery import BatteryModel
from simulator.model.subsystems.eps.EpsConfig import EpsConfigType, EpsDataType
from simulator.model.subsystems.Subsystem import Subsystem
from simulator.model.subsystems.eps.SolarPanel import SolarPanel


class EpsSubsystem(Subsystem):
    """
    The EPS subsystem manages all electrical generation and distribution
    for all other subsystems.  Other subsystems are responsible for calculating their specific power consumption.
    In the future may include a pyspice power model
    """
    def __init__(self, cubesat, power_config):
        """
        The EPS subsystem constructor.
        :param cubesat:
        :param power_config:
        """
        super().__init__("Power", cubesat,
                         power_config[EpsConfigType.EPS_MASS],
                         power_config[EpsConfigType.EPS_POWER],
                         power_config[EpsConfigType.EPS_DATA_GENERATION_RATE])
        self.panel_normals = []
        self.capacity_Wh: float = power_config[EpsConfigType.BATT_CAP]
        self.solar_area_m2: float = power_config[EpsConfigType.SOLAR_PANEL_AREA]
        self.generation_w: float = 0.0
        initial_soc = power_config[EpsConfigType.INITIAL_SOC]
        self.battery: BatteryModel = BatteryModel(initial_soc, capacity_Wh = self.capacity_Wh, nominal_voltage = 12)

        self.panels = [
            # +X face
            SolarPanel("Panel 1", normal_body=[1, 0, 0], area=self.solar_area_m2),
            SolarPanel("Panel 2", normal_body=[1, 0, 0], area=self.solar_area_m2),

            # -X face
            SolarPanel("Panel 3", normal_body=[-1, 0, 0], area=self.solar_area_m2),
            SolarPanel("Panel 4", normal_body=[-1, 0, 0], area=self.solar_area_m2),

            # +Y face
            SolarPanel("Panel 5", normal_body=[0, 1, 0], area=self.solar_area_m2),
            SolarPanel("Panel 6", normal_body=[0, 1, 0], area=self.solar_area_m2),

            # -Y face
            SolarPanel("Panel 7", normal_body=[0, -1, 0], area=self.solar_area_m2),
            SolarPanel("Panel 8", normal_body=[0, -1, 0], area=self.solar_area_m2),
        ]

    def update(self, dt: float, state) -> None:
        """
        Update method for the EPS subsystem.  currently a simplified sun model for generation
        :param dt: the duration of the timestep
        :param state: the state of the propagation
        :return:
        """

        generation_w = 0
        panel_w_set=[]
        for panel in self.panels:
            panel_w = panel.power(self.cubesat.q_body_eci, self.cubesat.sun_dir.eci, self.cubesat.illumination)
            panel_w_set.append(panel_w)
            generation_w += panel_w
        self.cubesat.data_store.eps_data[EpsDataType.PANEL_W].append(panel_w_set)
        self.generation_w = generation_w

        load_w = 0
        for subsystem in self.cubesat.subsystems:
            load_w += subsystem.get_power_draw()

        net_load = load_w-self.generation_w
        self.battery.step(net_load, dt)
        self.cubesat.data_store.eps_data[EpsDataType.BATTERY_SOC].append(self.battery.get_soc())
        self.cubesat.data_store.eps_data[EpsDataType.MAIN_BUS_V].append(self.battery.get_voltage())
