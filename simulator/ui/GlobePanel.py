# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import numpy as np
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox
from matplotlib.colors import LinearSegmentedColormap
from pyvistaqt import QtInteractor
import pyvista as pv
import matplotlib.pyplot as plt

from simulator.model.DataStore import SpacecraftDataType
from simulator.model.subsystems.payload.PayloadConfig import PayloadDataType


class GlobePanel(QWidget):
    """
    Panel containing the 3D Earth, the orbit and related vector fields with heatmap of field strength
    """
    def __init__(self, parent=None):
        """
        Constructor for the globe panel
        :param parent:
        """
        super().__init__(parent)

        self.payload_data = None
        self.orbit_data = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setup_checkboxes(layout)

        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter)
        self.init_earth_scene()

    def setup_checkboxes(self, parent_layout: QVBoxLayout) -> None:
        """
        Creates a horizontal layout with 4 checkboxes and adds it to the main layout.
        :param parent_layout:
        :return:
        """
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(5, 5, 5, 5)
        checkbox_layout.setAlignment(Qt.AlignLeft) # Align checkboxes to the left

        # Create the 4 checkboxes and store them as instance variables
        self.cb_mag = QCheckBox("Magnetic Field")
        self.cb_tether = QCheckBox("Tether Force")
        self.cb_nadir = QCheckBox("Nadir Direction")
        self.cb_heatmap = QCheckBox("Show Heatmaps")

        # Set some checkboxes to be checked by default if needed
        self.cb_tether.setChecked(True)
        self.cb_heatmap.setChecked(True)

        # Add them to the horizontal layout
        checkbox_layout.addWidget(self.cb_tether)
        checkbox_layout.addWidget(self.cb_mag)
        checkbox_layout.addWidget(self.cb_nadir)
        checkbox_layout.addWidget(self.cb_heatmap)

        self.cb_tether.stateChanged.connect(self.on_checkbox_state_changed)
        self.cb_mag.stateChanged.connect(self.on_checkbox_state_changed)
        self.cb_nadir.stateChanged.connect(self.on_checkbox_state_changed)
        self.cb_heatmap.stateChanged.connect(self.on_checkbox_state_changed)

        parent_layout.addLayout(checkbox_layout)

    @Slot(int)
    def on_checkbox_state_changed(self, state) -> None:
        self.update_plots(self.orbit_data, self.payload_data)

    def init_earth_scene(self) -> None:
        self.plotter.clear()

        tex = pv.read_texture(pv.examples.mapfile)
        tex = tex.flip_y()

        earth = pv.Sphere(radius=6371.0, theta_resolution=720, phi_resolution=360)
        earth.texture_map_to_sphere(inplace=True, prevent_seam=False)
        earth.clean(inplace=True)

        # Rotate
        angle_rad = np.deg2rad(180.0)
        rz = [
            [np.cos(angle_rad), -np.sin(angle_rad), 0],
            [np.sin(angle_rad), np.cos(angle_rad), 0],
            [0, 0, 1]
        ]
        earth.transform(rz, inplace=True)

        self.plotter.set_background("black")
        self.plotter.add_mesh(earth, texture=tex)
        self.plotter.show_axes()
        self.plotter.reset_camera()
        self.plotter.zoom_camera(1.5)

    def update_plots(self, orbit_data, payload_data) -> None:
        """
        Method to update the plots contained in the globe panel
        :param orbit_data: orbit data from the simulation to display
        :param payload_data: payload datq (e.g. tether force vectors) to display as vector field
        :return:
        """
        self.orbit_data = orbit_data
        self.payload_data = payload_data
        if hasattr(self.plotter, "scalar_bars"):
            for key in list(self.plotter.scalar_bars.keys()):
                try:
                    self.plotter.remove_scalar_bar(title=key)
                except Exception as e:
                    pass

        if orbit_data and payload_data:
            pos = [fv.ecef/1000.0 for fv in orbit_data[SpacecraftDataType.POSITION]]
            mag = [fv.ecef for fv in orbit_data[SpacecraftDataType.MAG_FIELD]]
            tether = [fv.ecef for fv in payload_data[PayloadDataType.TETHER_FORCE]]
            nadir = [fv.ecef for fv in orbit_data[SpacecraftDataType.NADIR_VECTOR]]

            pos = np.array(pos) if isinstance(pos, list) else pos
            mag = np.array(mag) if isinstance(mag, list) else mag
            tether = np.array(tether) if isinstance(tether, list) else tether
            nadir = np.array(nadir) if isinstance(nadir, list) else nadir

            n_points = len(pos)
            lines = np.hstack([[n_points], np.arange(n_points)])  # simple connected polyline
            orbit_line = pv.PolyData(pos, lines=lines)
            self.plotter.add_mesh(orbit_line, color="grey", line_width=3, name="orbit")  # orbit path

            self.render_on_globe("mag arrows", "Magnetic Field (T)", pos, mag,
                                 "green", "Greens", self.cb_heatmap.isChecked(),
                                 0.75, self.cb_mag.isChecked(), 1)
            self.render_on_globe("force arrows", "Tether Force (N)", pos, tether,
                                 "red", "Reds", self.cb_heatmap.isChecked(),
                                 0.05, self.cb_tether.isChecked(), 1)
            self.render_on_globe("nadir arrows", "Tether Direction", pos, nadir,
                                 "yellow", "Yellows", False,
                                 0.0, self.cb_nadir.isChecked(), 0.5)

    def render_on_globe(self, actor_name, title, pos, vectors, colour, cmap_name, heatmap, v_offset, show, scale):
        if show:
            arrow_scale = 500.0*scale
            vec_norm = np.linalg.norm(vectors, axis=1)
            vec_norm[vec_norm == 0] = 1e-9
            vec_dir = vectors / vec_norm[:, None]
            arrow_vector = vec_dir * arrow_scale
            points = pv.PolyData(pos)
            points["vectors"] = arrow_vector
            points["magnitude"] = vec_norm

            # Create arrows
            arrows = points.glyph(
                orient="vectors",
                scale=True,
                geom=pv.Arrow(),
                factor=1.0
            )

            if heatmap:
                cmap = plt.get_cmap(cmap_name)
                cmap = LinearSegmentedColormap.from_list(colour+"_trunc", cmap(np.linspace(0.3, 0.9, 256)))
                self.plotter.add_mesh(
                    arrows,
                    scalars="magnitude",
                    cmap=cmap,
                    clim=[points["magnitude"].min(), points["magnitude"].max()],
                    name=actor_name,
                    scalar_bar_args={
                        "title": title,  # optional title
                        "title_font_size": 14,
                        "label_font_size": 12,
                        "color": "grey",  # text color
                        "n_labels": 5,  # number of tick labels
                        "vertical": True,  # orientation
                        "height": 0.2,  # fraction of the window height
                        "width": 0.05,  # fraction of the window width
                        "position_x": 0.90,  # horizontal placement
                        "position_y": v_offset  # vertical placement
                    }
                )
            else:
                self.plotter.add_arrows(pos, arrow_vector, color=colour, mag=1.0, name=actor_name)
        else:
            self.plotter.remove_actor(actor_name)
