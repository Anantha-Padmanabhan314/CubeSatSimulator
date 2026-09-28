# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.
import csv
from enum import Enum

import numpy as np

from simulator.model.subsystems.adcs.AdcsConfig import AdcsDataType
from simulator.model.subsystems.comms.CommsConfig import CommsDataType
from simulator.model.subsystems.ground.GroundConfig import GroundDataType
from simulator.model.subsystems.payload.PayloadConfig import PayloadDataType
from simulator.model.subsystems.eps.EpsConfig import EpsDataType
from simulator.model.subsystems.structure.StructureConfig import StructureDataType


class TimeDataType(str, Enum):
    """
    The time related dataset types, to serve as the time reference for all other dataset data items
    """
    ELAPSED_TIME = "Mission Elapsed Time"
    DATE = "Date"


class SpacecraftDataType(str, Enum):
    """
    The various spacecraft-level types for dataset information
    """
    ALTITUDE = "Altitude"
    INCLINATION = "Inclination"
    ECCENTRICITY = "Eccentricity"
    ILLUMINATION = "Illumination Fraction"
    MAG_FIELD = "Magnetic Field"
    NADIR_VECTOR = "Nadir Vector"
    POSITION = "Position"
    VELOCITY = "Velocity"
    ACCELERATION = "Acceleration"
    SUN_DIR = "Sun Vector"
    Q_ECI = "Quaternion"
    RPY_ECI = "Roll, Pitch, Yaw"
    Q_LVLH = "Quaternion: Local Vertical Local Horizontal"
    RPY_LVLH = "Roll, Pitch, Yaw: Local Vertical Local Horizontal"


class DataStore:
    """
    The DatqStore class stores time-series data for various properties of the CubeSat and associated subsystems.
    This time-series data is then available for display and trend charting
    """
    def __init__(self):
        """
        Constructor for the datastore class.
        """
        self.time_data = {dtype: [] for dtype in TimeDataType}
        self.spacecraft_data = {dtype: [] for dtype in SpacecraftDataType}

        self.payload_data = {dtype: [] for dtype in PayloadDataType}
        self.comms_data = {dtype: [] for dtype in CommsDataType}
        self.eps_data = {dtype: [] for dtype in EpsDataType}
        self.structure_data = {dtype: [] for dtype in StructureDataType}
        self.adcs_data = {dtype: [] for dtype in AdcsDataType}
        self.ground_data = {dtype: [] for dtype in GroundDataType}

    def export_single_csv(self, filename):
        """
        Export all subsystem data into a single CSV file.
        Each row = one signal.
        Rows with all-zero or empty values are omitted.
        First element of each row = signal name.
        """

        # Merge all subsystem dicts into one large dict
        merged = {
            **self.time_data,
            **self.spacecraft_data,
            **self.payload_data,
            **self.comms_data,
            **self.eps_data,
            **self.structure_data,
            **self.adcs_data,
            **self.ground_data,
        }

        # Convert enum keys → readable strings
        formatted = {str(k): v for k, v in merged.items()}

        # Determine longest time series
        max_len = max((len(v) for v in formatted.values() if v), default=0)

        def value_is_meaningful(x):
            """Return True if x contains non-zero / non-empty data."""
            if x is None:
                return False
            if isinstance(x, str):
                return x.strip() != ""
            if isinstance(x, (int, float)):
                return x != 0
            if isinstance(x, (list, tuple)):
                return any(value_is_meaningful(v) for v in x)
            if isinstance(x, np.ndarray):
                return np.any(x != 0)
            return True  # fallback for unexpected types

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)

            for name, series in formatted.items():
                if not series:
                    continue

                # Skip rows where ALL entries are zero/empty
                if not any(value_is_meaningful(v) for v in series):
                    continue

                # Pad shorter series
                padded = list(series) + [""] * (max_len - len(series))

                writer.writerow([name] + padded)
