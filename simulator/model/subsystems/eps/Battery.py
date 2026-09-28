# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import numpy as np


class BatteryModel:
    """
    Simple battery model with SOC, and charge/discharge I/V curves
    """
    def __init__(self, init_soc: float, capacity_Wh: float, nominal_voltage: float):
        """
        BatteryModel Constructor.
        :param capacity_Wh:
        :param nominal_voltage:
        """
        self.soc_points = np.linspace(0, 1, 21)
        self.v_charge = [
            3.00, 3.20, 3.35, 3.45, 3.55,
            3.65, 3.70, 3.75, 3.80, 3.85,
            3.90, 3.95, 4.00, 4.05, 4.10,
            4.12, 4.15, 4.17, 4.18, 4.19,
            4.20
        ]
        self.v_discharge = [
            3.00, 3.15, 3.30, 3.40, 3.50,
            3.60, 3.65, 3.70, 3.75, 3.80,
            3.83, 3.86, 3.88, 3.90, 3.92,
            3.95, 3.98, 4.00, 4.02, 4.05,
            4.10
        ]
        self.capacity_Wh = capacity_Wh
        self.nominal_voltage = nominal_voltage
        self.energy_Wh = capacity_Wh * init_soc
        self.is_charging = False

        # Interpolation functions
        self.v_from_soc_charge = lambda soc: np.interp(soc, self.soc_points, self.v_charge)
        self.v_from_soc_discharge = lambda soc: np.interp(soc, self.soc_points, self.v_discharge)

    def step(self, power_W: float, dt_s) -> None:
        """
        Advance the battery model by dt_s seconds given eps draw (W).
        Positive power_W = discharge, negative = charge.
        """
        dE_Wh = (power_W * dt_s) /3600
        new_energy = np.clip(self.energy_Wh - dE_Wh, 0, self.capacity_Wh)
        self.is_charging = power_W < 0
        self.energy_Wh = new_energy

    def get_voltage(self) -> float:
        """
        Method to return the current voltage based on wether it's charging or discharging
        :return:
        """
        soc = self.energy_Wh / self.capacity_Wh
        if self.is_charging:
            return self.v_from_soc_charge(soc)
        else:
            return self.v_from_soc_discharge(soc)

    def get_soc(self) -> float:
        """
        Method to return the stat of charge fraction
        :return:
        """
        return self.energy_Wh / self.capacity_Wh