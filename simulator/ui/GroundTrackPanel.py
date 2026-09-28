# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import cartopy.crs as ccrs
import numpy as np
import cartopy.feature as cfeature
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout
from simulator.model.subsystems.ground.GroundConfig import GroundDataType, GroundConfigType

BG_COLOR = "grey"
CONTACT_COLOR = 'red'


class GroundTrackPanel(QWidget):
    """
    A Ground Track map-based panel that shows the ground track path of the orbit, along with periods of ground contact
    with selected stations.  Stations are also shown on the map.
    """
    def __init__(self, ground_config, stations, parent=None):
        """
        Constructor for the ground track panel
        :param ground_config: The current ground configuration
        :param stations: The currently set of selected stations for the simulation
        :param parent: A parent panel
        """
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(facecolor=BG_COLOR)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.ground_config = ground_config
        self.stations = stations
        self.ax = self.figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        self.figure.subplots_adjust(left=0.03, right=0.97, top=0.98, bottom=0.02, wspace=0.1, hspace=0.1)

        self.setup_map()

    def setup_map(self) -> None:
        """
        Configures the map appearance.
        :return:
        """
        self.ax.set_global()
        self.ax.add_feature(cfeature.LAND, color='black')
        self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='gray')
        self.ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')
        self.ax.add_feature(cfeature.OCEAN, color='darkblue', alpha=0.5)
        self.ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        self.ax.set_title("Satellite Ground Track")

    def update_plots(self, ground_data) -> None:
        """
        Method to update the plots contained in the ground track panel
        :param orbit_data: Orbit data for display on the ground track
        :param ground_data: Ground data for display on the ground track
        :return:
        """
        for line in self.ax.lines:
            line.remove()

        latitudes = np.asarray(ground_data[GroundDataType.SAT_NADIR_LAT])
        longitudes = np.asarray(ground_data[GroundDataType.SAT_NADIR_LONG])
        vis = np.asarray(ground_data[GroundDataType.GROUND_VISIBLE])

        # --- Manual Segmentation Logic ---
        lon_segment, lat_segment = [], []
        if len(longitudes) == 0:
            self.canvas.draw()
            return

        current_vis = vis[0]
        lon_segment.append(longitudes[0])
        lat_segment.append(latitudes[0])

        # Iterate from the second point onwards
        for i in range(1, len(longitudes)):
            prev_lon = longitudes[i - 1]
            curr_lon = longitudes[i]
            curr_lat = latitudes[i]
            curr_vis = vis[i]

            # Condition 1: Anti-meridian crossing (large jump) - BREAK the line
            if abs(curr_lon - prev_lon) > 300:
                # Finish and plot the current segment (doesn't include the current point)
                if len(lon_segment) > 1:
                    color = CONTACT_COLOR if current_vis else 'cyan'
                    self.ax.plot(lon_segment, lat_segment, color=color, linewidth=2, transform=ccrs.PlateCarree())

                # Start a new segment with the current point
                lon_segment, lat_segment = [curr_lon], [curr_lat]
                current_vis = curr_vis

            # Condition 2: Visibility status change - BREAK the line but overlap points
            elif curr_vis != current_vis:
                # Add current point to the *end* of the old segment to close the gap visually
                lon_segment.append(curr_lon)
                lat_segment.append(curr_lat)

                # Plot the old segment
                if len(lon_segment) > 1:
                    color = CONTACT_COLOR if current_vis else 'cyan'
                    self.ax.plot(lon_segment, lat_segment, color=color, linewidth=2, transform=ccrs.PlateCarree())

                # Start a new segment, *starting* with the same current point to close the gap
                lon_segment, lat_segment = [curr_lon], [curr_lat]
                current_vis = curr_vis

            # Condition 3: No special event, continue the current segment
            else:
                lon_segment.append(curr_lon)
                lat_segment.append(curr_lat)

        # Plot the final segment after the loop finishes
        if len(lon_segment) > 1:
            color = CONTACT_COLOR if current_vis else 'cyan'
            self.ax.plot(lon_segment, lat_segment, color=color, linewidth=2, transform=ccrs.PlateCarree())

        stn_latitudes = []
        stn_longitudes = []
        for station in self.stations:
            stn_latitudes.append(station['lat'])
            stn_longitudes.append(station['lng'])

        self.plot_locations(stn_latitudes, stn_longitudes)
        self.canvas.draw()

    def plot_locations(self, latitudes, longitudes, marker='x', color='yellow', size=50) -> None:
        """
        Method to plot station locations on the map
        :param latitudes: station latitude
        :param longitudes: station longitude
        :param marker: Type of marker to use to mark station
        :param color: The colour used to mark the station
        :param size: The size of the marker to mark on the station
        :return:
        """
        # latitudes and longitudes can be single values or lists
        if not isinstance(latitudes, (list, tuple, np.ndarray)):
            latitudes = [latitudes]
        if not isinstance(longitudes, (list, tuple, np.ndarray)):
            longitudes = [longitudes]

        # Use ax.scatter() with the reliable standard 'x' marker
        self.ax.scatter(longitudes, latitudes, c=color, s=size, marker=marker, transform=ccrs.PlateCarree(), zorder=5)
        self.canvas.draw()

    def update_config(self, ground_config, stations) -> None:
        """
        A method to update the configuration shown in the subsystem panel
        :param ground_config: the ground station config parameters
        :param stations: the set of stations currently selected for the simulation
        :return:
        """
        self.stations = stations
        self.ground_config = ground_config

