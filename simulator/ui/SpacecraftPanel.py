# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from simulator.model.DataStore import SpacecraftDataType
from simulator.model.ModelConfig import ConfigType
from simulator.ui.AttitudePanel import AttitudePanel
from simulator.ui.GlobePanel import GlobePanel
from simulator.ui.SubsystemPanel import SubsystemPanel


class SpacecraftPanel(QWidget):
    """
    A Spacecraft-level panel, comprised of a 3D globe representation of the orbit and related vector fields,
    an attitude panel showing the attitude of the spacecraft, and a spacecraft config and results plotting panel
    """
    def __init__(self, spacecraft_config, structure_config, parent=None):
        """
        Constructor for the Spacecraft panel
        :param spacecraft_config: The spacecraft-level config parameters
        :param structure_config: The structure-subsystem-level config parameters
        :param parent:
        """
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.spacecraft_panel = SubsystemPanel(ConfigType, SpacecraftDataType, spacecraft_config)
        self.attitude_panel = AttitudePanel(structure_config, self)
        self.globe_panel = GlobePanel(self)

        self.tabs.addTab(self.globe_panel, "Orbit and Vector Fields")
        self.tabs.addTab(self.attitude_panel, "Spacecraft Attitude")
        self.tabs.addTab(self.spacecraft_panel, "Spacecraft Config and Data")

    def update_plots(self, times, spacecraft_data, payload_data) -> None:
        """
        Method to update the plots contained in all lower level panels
        :param times: The times related to the data to plot
        :param spacecraft_data: The spacecraft-level data to plot
        :param payload_data: The payload-subsystem-level data to plot
        :return:
        """
        self.spacecraft_panel.update_plots(times, spacecraft_data)
        self.attitude_panel.update_plots(times, spacecraft_data)
        self.globe_panel.update_plots(spacecraft_data, payload_data)
    def update_config(self, config) -> None:
        """
        A method to update the configuration shown in config-type panels
        :param config:
        :return:
        """
        self.spacecraft_panel.update_config(config)
