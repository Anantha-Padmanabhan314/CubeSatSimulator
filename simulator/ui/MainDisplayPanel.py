# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.
from queue import Queue

from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from simulator.model import ModelConfig
from simulator.model.DataStore import DataStore, TimeDataType
from simulator.model.subsystems.adcs.AdcsConfig import AdcsConfigType, AdcsDataType
from simulator.model.subsystems.comms.CommsConfig import CommsDataType, CommsConfigType
from simulator.model.subsystems.payload.PayloadConfig import PayloadConfigType, PayloadDataType
from simulator.model.subsystems.eps.EpsConfig import EpsConfigType, EpsDataType
from simulator.model.subsystems.structure.StructureConfig import StructureConfigType, StructureDataType
from simulator.ui.GroundPanel import GroundPanel
from simulator.ui.LogPanel import LogPanel
from simulator.ui.SpacecraftPanel import SpacecraftPanel
from simulator.ui.ControlAndStatusPanel import ControlAndStatusPanel
from simulator.ui.SubsystemPanel import SubsystemPanel


class MainDisplayPanel(QWidget):
    """
    The main display panel for the CubeSat simulator application
    """
    def __init__(self, cmd_queue: Queue, status_queue: Queue, config: ModelConfig, parent=None):
        """
        Constructor for the main display panel
        :param cmd_queue: The queue for submitting command messages for the simulator
        :param status_queue: The queue for receiving status messages from the simulator
        :param config: The ModelConfig data for the simulation
        :param parent:
        """
        super().__init__(parent)

        self.log_panel = LogPanel()
        self.spacecraft_panel = SpacecraftPanel(config.spacecraft_config, config.structure_config)

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(5)
        self.setLayout(main_layout)

        # -----------------------
        # Tabbed central area
        # -----------------------
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)

        self.eps_panel = SubsystemPanel(EpsConfigType, EpsDataType, config.eps_config)
        self.adcs_panel = SubsystemPanel(AdcsConfigType, AdcsDataType, config.adcs_config)
        self.structure_panel = SubsystemPanel(StructureConfigType, StructureDataType, config.structure_config)
        self.comms_panel = SubsystemPanel(CommsConfigType, CommsDataType, config.comms_config)
        self.payload_panel = SubsystemPanel(PayloadConfigType, PayloadDataType, config.payload_config)
        self.ground_panel = GroundPanel(config.ground_config, config.stations)

        # Example tabs
        self.tabs.addTab(self.spacecraft_panel, "Spacecraft")
        self.tabs.addTab(self.eps_panel, "EPS")
        self.tabs.addTab(self.adcs_panel, "ADCS")
        self.tabs.addTab(self.comms_panel, "Comms")
        self.tabs.addTab(self.structure_panel, "Structure")
        self.tabs.addTab(self.payload_panel, "Payload")
        self.tabs.addTab(self.ground_panel, "Ground")
        self.tabs.addTab(self.log_panel, "Log")

        self.status_panel = ControlAndStatusPanel(config, cmd_queue, status_queue, self)
        main_layout.addWidget(self.status_panel)

    # Expose some convenience methods
    def set_status_text(self, text: str) -> None:
        """
        Method to set the status text on the main display
        :param text:
        :return:
        """
        self.status_panel.set_text(text)

    def set_progress(self, value: int) -> None:
        """
        Method to set the simulation progress on the main display progress bar
        :param value: The progress value
        :return:
        """
        self.status_panel.set_progress(value)

    def reset_progress(self) -> None:
        """
        Method to reset the simulation progress on the main display progress bar
        :return:
        """
        self.status_panel.reset_progress()

    def update_results(self, data: DataStore) -> None:
        """
        Method to update the results displayed in various lower level panels
        :param data: The DataStore of collected data/results from the simulation
        :return:
        """
        if data and data.time_data[TimeDataType.ELAPSED_TIME]:
            times = data.time_data[TimeDataType.ELAPSED_TIME]
            self.spacecraft_panel.update_plots(times, data.spacecraft_data, data.payload_data)
            self.eps_panel.update_plots(times, data.eps_data)
            self.comms_panel.update_plots(times, data.comms_data)
            self.adcs_panel.update_plots(times, data.adcs_data)
            self.structure_panel.update_plots(times, data.structure_data)
            self.payload_panel.update_plots(times, data.payload_data)
            self.ground_panel.update_plots(data.ground_data)

    def update_config(self, config: ModelConfig) -> None:
        """
        A method to update the configuration shown in lower level panels
        :param config: The updated model configuration
        :return:
        """
        self.spacecraft_panel.update_config(config.spacecraft_config)
        self.eps_panel.update_config(config.eps_config)
        self.comms_panel.update_config(config.comms_config)
        self.adcs_panel.update_config(config.adcs_config)
        self.structure_panel.update_config(config.structure_config)
        self.payload_panel.update_config(config.payload_config)
        self.ground_panel.update_config(config.ground_config, config.stations)

