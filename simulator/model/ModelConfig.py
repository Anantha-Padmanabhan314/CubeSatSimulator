# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum
import numpy as np

from simulator.model.subsystems.adcs.AdcsConfig import AdcsConfigType
from simulator.model.subsystems.comms.CommsConfig import CommsConfigType
from simulator.model.subsystems.ground.GroundConfig import GroundConfigType
from simulator.model.subsystems.payload.PayloadConfig import PayloadConfigType
from simulator.model.subsystems.eps.EpsConfig import EpsConfigType
from simulator.model.subsystems.structure.StructureConfig import StructureConfigType


class ConfigType(str, Enum):
    """
    The spacecraft-level config types.  Note that subsystems maintain their own separate ConfigTypes
    per imports above.
    """
    ALT = "Altitude"
    INC = "Inclination"
    ECC = "Eccentricity"
    OMEGA = "Argument of Periapsis"
    RAAN = "Right Ascension of the Ascending Node"
    LM = "Mean Anomaly"
    Q0_0 = "Initial Attitude Quaternion - 0th element"
    Q0_1 = "Initial Attitude Quaternion - 1st element"
    Q0_2 = "Initial Attitude Quaternion - 2nd element"
    Q0_3 = "Initial Attitude Quaternion - 3rd element"
    W0_0 = "Initial Attitude Rate - 0th element"
    W0_1 = "Initial Attitude Rate - 1st element"
    W0_2 = "Initial Attitude Rate - 2nd element"

class NotesType(str, Enum):
    """
    A notes type for note configuration
    """
    NOTES = "Notes"


class Config:
    """
    The Config class contains all the configurable elements for
    the CubeSat and related subsystems.  The GUI will populate configuration widgets based on the
    set of configuration parameters available in this and associated subsystem config classes.

    The Config instance can be saved/loaded via the pickle library for saving specific spacecraft configurations
    """
    def __init__(self):
        """
        Constructor for the Config class.
        """
        self.name = "Demo SAT"
        self.start_date = "2027-01-01T00:00:00Z"
        self.duration = 1
        self.step_size = 60
        self.spacecraft_config = {}
        self.eps_config = {}
        self.comms_config = {}
        self.payload_config = {}
        self.adcs_config = {}
        self.structure_config = {}
        self.ground_config = {}
        self.stations = []

    def __str__(self):
        """
        Override the str method to provide a human-readable output of the current configuration
        :return:
        """
        return (
            f"Config(\n"
            f"  name={self.name}\n"
            f"  spacecraft_config={self.spacecraft_config},\n"
            f"  power_config={self.eps_config},\n"
            f"  comms_config={self.comms_config},\n"
            f"  payload_config={self.payload_config},\n"
            f"  adcs_config={self.adcs_config},\n"
            f"  structure_config={self.structure_config}\n"
            f"  ground_config={self.ground_config}\n"         
            f")"
        )


def get_default_config():
    """
    Function to return a default Config prepopulated with default values
    :return:
    """
    config = Config()
    config.spacecraft_config[ConfigType.ALT] = 300
    config.spacecraft_config[ConfigType.INC] = 80
    config.spacecraft_config[ConfigType.ECC] = 0.001
    config.spacecraft_config[ConfigType.OMEGA] = 0
    config.spacecraft_config[ConfigType.RAAN] = 0
    config.spacecraft_config[ConfigType.LM] = 0
    config.spacecraft_config[ConfigType.Q0_0] = 0.7071
    config.spacecraft_config[ConfigType.Q0_1] = 0
    config.spacecraft_config[ConfigType.Q0_2] = 0
    config.spacecraft_config[ConfigType.Q0_3] = 0.7071
    config.spacecraft_config[ConfigType.W0_0] = -0.00116
    config.spacecraft_config[ConfigType.W0_1] = 0
    config.spacecraft_config[ConfigType.W0_2] = 0

    config.eps_config[EpsConfigType.INITIAL_SOC] = 0.8
    config.eps_config[EpsConfigType.BATT_CAP] = 20
    config.eps_config[EpsConfigType.EPS_MASS] = 1
    config.eps_config[EpsConfigType.EPS_POWER] = 0.25
    config.eps_config[EpsConfigType.SOLAR_PANEL_AREA] = 0.0072
    config.eps_config[EpsConfigType.EPS_DATA_GENERATION_RATE] = 100

    '''
    Representative starting values for a bare-tether design, 
    not validated against a specific mission, tune for your actual hardware.
    '''
    
    config.payload_config[PayloadConfigType.TETHER_BARE_LEN] = 100        # L_b, m
    config.payload_config[PayloadConfigType.TETHER_INSULATED_LEN] = 400   # L_i, m
    config.payload_config[PayloadConfigType.TETHER_CONDUCTIVITY] = 3.5e7  # sigma_t, S/m (aluminum)
    config.payload_config[PayloadConfigType.TETHER_CROSS_SECTION_AREA] = 7.85e-7  # A_t, m^2 (~0.5mm-radius round wire)
    config.payload_config[PayloadConfigType.TETHER_PERIMETER] = 3.14e-3   # p_t, m
    config.payload_config[PayloadConfigType.TETHER_AEE_POTENTIAL] = -1.0  # V_C, V
    config.payload_config[PayloadConfigType.PAYLOAD_MASS] = 1
    config.payload_config[PayloadConfigType.PAYLOAD_POWER] = 1.5
    config.payload_config[PayloadConfigType.PAYLOAD_DATA_GENERATION_RATE] = 200

    config.adcs_config[AdcsConfigType.ADCS_MASS] = 1
    config.adcs_config[AdcsConfigType.ADCS_POWER] = 0.5
    config.adcs_config[AdcsConfigType.ADCS_DATA_GENERATION_RATE] = 100
    config.adcs_config[AdcsConfigType.WHEEL_INERTIA] = 0.0012
    config.adcs_config[AdcsConfigType.MAX_WHEEL_SPEED] = 6000 * np.pi / 30
    config.adcs_config[AdcsConfigType.MAX_WHEEL_ACCEL] = 0.1
    config.adcs_config[AdcsConfigType.WHEEL_EFFICIENCY] = 0.85
    config.adcs_config[AdcsConfigType.WHEEL_IDLE_POWER_COEFF] = 0.02

    config.comms_config[CommsConfigType.COMMS_MASS] = 1
    config.comms_config[CommsConfigType.COMMS_POWER] = 1
    config.comms_config[CommsConfigType.COMMS_TX_POWER] = 5
    config.comms_config[CommsConfigType.TX_DATARATE] = 32768
    config.comms_config[CommsConfigType.DATA_STORAGE_CAPACITY] = 1073741824

    config.structure_config[StructureConfigType.STRUCTURE_MASS] = 1
    config.structure_config[StructureConfigType.DRAG_AREA] = 0.03
    config.structure_config[StructureConfigType.DRAG_COEF] = 1
    config.structure_config[StructureConfigType.I_XX] = 10
    config.structure_config[StructureConfigType.I_YY] = 10
    config.structure_config[StructureConfigType.I_ZZ] = 10
    config.structure_config[StructureConfigType.MODEL_FILE_3D] = "3UCubeSat.ply"

    config.ground_config[GroundConfigType.STATIONS] = {"VE2DSK-VHF-UHF", "ZL2CWA Hamilton NZ", "Dunchurch", "UVSD-SatNOGS"}
    config.ground_config[GroundConfigType.BAND_FILTER] = "VHF"

    return config
