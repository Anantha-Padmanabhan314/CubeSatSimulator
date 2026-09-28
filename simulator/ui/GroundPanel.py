# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from simulator.ui.GroundTrackPanel import GroundTrackPanel
from simulator.ui.SatnogsPanel import SatNOGSPanel


class GroundPanel(QWidget):
    """
    A Ground subsystem panel for displaying satellite ground track and station contact periods,
    and to provide a station selection map.
    """
    def __init__(self, ground_config, stations, parent=None):
        """
        Constructor for the ground panel
        :param ground_config:
        :param stations:
        :param parent:
        """
        super().__init__(parent)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.stations_panel = SatNOGSPanel(ground_config)
        self.ground_track_panel = GroundTrackPanel(ground_config, stations, self)

        # Example starter tabs (can be replaced later)
        self.tabs.addTab(self.ground_track_panel, "Ground Track")
        self.tabs.addTab(self.stations_panel, "Station Selection")

    def update_plots(self, ground_data) -> None:
        """
        Method to update the plots contained in the subsystem panel

        :param ground_data: Ground data for display on the ground track
        :return:
        """
        self.ground_track_panel.update_plots(ground_data)

    def update_config(self, ground_config, stations) -> None:
        """
        A method to update the configuration shown in the subsystem panel
        :param ground_config:
        :param stations:
        :return:
        """
        self.ground_track_panel.update_config(ground_config, stations)
