# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.
from pathlib import Path

import numpy as np
import pyvista as pv
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget, QLabel, QSlider, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout
from pyvistaqt import QtInteractor

from simulator.model import Utilities
from simulator.model.DataStore import SpacecraftDataType
from simulator.model.subsystems.structure.StructureConfig import StructureConfigType


class AttitudePanel(QWidget):
    """
    Attitude panel, showing either ECI or Local Horizontal/Local Vertical frame with attitude
    rendered via 3D model of the CubeSat
    """
    def __init__(self, structure_config, parent=None):
        """
        AttitudePanel constructor
        :param structure_config: The Structure config parameters
        :param parent: the parent panel
        """
        super().__init__(parent)

        resources_dir = Path(__file__).resolve().parent.parent.parent / "resources"
        self.mesh = pv.read(str(resources_dir / structure_config[StructureConfigType.MODEL_FILE_3D]))
        self.base_points = self.mesh.points.copy()
        self.center = self.mesh.center

        self.sun_dir_lvlh = []
        self.sun_dir_eci = []
        self.lvlh_qs = []
        self.eci_qs = []
        self.illumination = []
        self.times = []
        self.use_eci = True

        self.arrow_nadir = None
        self.arrow_vel = None

        # === Animation state ===
        self.playing = False
        self.timer = QTimer()
        self.timer.setInterval(40)  # 25 fps
        self.timer.timeout.connect(self.advance_frame)

        # === Play/Pause Button ===
        self.btn_play = QPushButton("Play ▶")
        self.btn_play.setCheckable(True)
        self.btn_play.toggled.connect(self.toggle_play)

        # PyVista widget
        self.pv_widget = QtInteractor(self, lighting='none')

        self.pv_widget.set_background("black")
        self.pv_widget.add_mesh(
            self.mesh,
            show_edges=False,
            rgb=True,
            scalar_bar_args=None,
            ambient=0.5)

        camera = self.pv_widget.camera

        self.sun_light = pv.Light()
        self.sun_light.light_type = pv.Light.SCENE_LIGHT
        self.sun_light.position = (30, 0, 0)
        self.sun_light.focal_point = (0, 0, 0)
        self.sun_light.SetColor(1.0, 1.0, 1.0)
        self.sun_light.intensity = 10
        self.pv_widget.add_light(self.sun_light)

        camera.clipping_range = (0.1, 5000)
        camera.focal_point = self.center
        camera.position = (self.center[0], self.center[1], self.center[2] + 1.5)
        camera.up = (-1, 0, 0)
        self.pv_widget.update()
        self.pv_widget.render()

        # Custom axes
        axes = self.pv_widget.add_axes(interactive=False)
        for axis in [
            axes.GetXAxisCaptionActor2D(),
            axes.GetYAxisCaptionActor2D(),
            axes.GetZAxisCaptionActor2D()
        ]:
            prop = axis.GetCaptionTextProperty()
            prop.SetColor(1, 1, 1)
            prop.BoldOn()
            prop.SetFontSize(18)

        axes.SetXAxisLabelText("x")
        axes.SetYAxisLabelText("y")
        axes.SetZAxisLabelText("z")

        # Time label
        self.label = QLabel(f"Time: 00:00:00")
        self.label.setAlignment(Qt.AlignCenter)

        # === ECI Checkbox ===
        self.cb_eci = QCheckBox("Use ECI attitude")
        self.cb_eci.setChecked(True)
        self.cb_eci.stateChanged.connect(self.toggle_frame)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.update_attitude)

        # Tick labels widget
        self.tick_labels = SliderLabels([], num_labels=0)
        self.tick_labels.setFixedHeight(20)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.pv_widget.interactor)
        layout.addWidget(self.cb_eci)
        layout.addWidget(self.label)

        # Play + Slider layout
        hbox = QHBoxLayout()
        hbox.addWidget(self.btn_play)
        hbox.addWidget(self.slider)
        layout.addLayout(hbox)

        layout.addWidget(self.tick_labels)
        self.setLayout(layout)


    # ---------------------------------------------
    # PLAY / PAUSE HANDLING
    # ---------------------------------------------
    def toggle_play(self, playing):
        self.playing = playing
        if playing:
            self.btn_play.setText("Pause ❚❚")
            self.timer.start()
        else:
            self.btn_play.setText("Play ▶")
            self.timer.stop()

    def advance_frame(self):
        """Advance one frame per timer tick."""
        idx = self.slider.value() + 1
        if idx >= len(self.times):
            idx = 0  # loop animation
        self.slider.setValue(idx)

    # ---------------------------------------------
    def toggle_frame(self, state):
        self.use_eci = self.cb_eci.isChecked()
        self.update_attitude(self.slider.value())

    def update_attitude(self, idx):
        if len(self.times) == 0:
            return

        q = self.eci_qs[min(idx, len(self.eci_qs) - 1)]
        if not self.use_eci:
            q = self.lvlh_qs[min(idx, len(self.lvlh_qs) - 1)]

        R = Utilities.quat_to_rotmat(q)

        # Rotate spacecraft
        self.mesh.points[:] = (R @ (self.base_points - self.center).T).T + self.center

        # --- Update Sun Light ---
        sun_vec = self.sun_dir_eci[min(idx, len(self.sun_dir_eci) - 1)]
        if not self.use_eci:
            sun_vec = self.sun_dir_lvlh[min(idx, len(self.sun_dir_lvlh) - 1)]
        sun_vec /= (np.linalg.norm(sun_vec) + 1e-9)

        SUN_DISTANCE = 50.0
        sun_pos = self.center + sun_vec * SUN_DISTANCE

        self.sun_light.position = sun_pos
        self.sun_light.focal_point = self.center
        self.sun_light.intensity = 10 * self.illumination[min(idx, len(self.illumination) - 1)]

        # Render update
        self.pv_widget.update()

        h = int(self.times[idx])
        m = int(self.times[idx] * 60) % 60
        s = int(self.times[idx] * 3600) % 60
        self.label.setText(f"Time: {h:02d}:{m:02d}:{s:02d}")

        # ------------------------------------------------
        # Update Velocity and Nadir Arrows
        # ------------------------------------------------
        if self.use_eci:
            vel_vec = self.vel_eci[min(idx, len(self.vel_eci) - 1)]
            nadir_vec = self.nadir_eci[min(idx, len(self.nadir_eci) - 1)]
        else:
            vel_vec = self.vel_lvlh[min(idx, len(self.vel_lvlh) - 1)]
            nadir_vec = self.nadir_lvlh[min(idx, len(self.nadir_lvlh) - 1)]

        # Normalize
        vel_vec = vel_vec / (np.linalg.norm(vel_vec) + 1e-9)
        nadir_vec = nadir_vec / (np.linalg.norm(nadir_vec) + 1e-9)

        # Add/update arrows
        self._update_arrow("arrow_vel", vel_vec, color=(0.2, 1.0, 0.2))  # green
        self._update_arrow("arrow_nadir", nadir_vec, color=(1.0, 0.2, 0.2))  # red


    def update_plots(self, times, spacecraft_data):
        self.times = times
        self.lvlh_qs = spacecraft_data[SpacecraftDataType.Q_LVLH]
        self.eci_qs = spacecraft_data[SpacecraftDataType.Q_ECI]

        sun_dirs = spacecraft_data[SpacecraftDataType.SUN_DIR]
        self.sun_dir_eci = [fv.eci for fv in sun_dirs]
        self.sun_dir_lvlh = [fv.lvlh for fv in sun_dirs]

        self.vel_eci = [fv.eci for fv in spacecraft_data[SpacecraftDataType.VELOCITY]]
        self.vel_lvlh = [fv.lvlh for fv in spacecraft_data[SpacecraftDataType.VELOCITY]]

        self.nadir_eci = [fv.eci for fv in spacecraft_data[SpacecraftDataType.NADIR_VECTOR]]
        self.nadir_lvlh = [fv.lvlh for fv in spacecraft_data[SpacecraftDataType.NADIR_VECTOR]]

        self.illumination = spacecraft_data[SpacecraftDataType.ILLUMINATION]

        self.tick_labels.update_config(times)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.times) - 1)
        self.slider.setTickInterval(max(1, len(self.times)//4))

    def _update_arrow(self, arrow_attr_name, direction_vec, color):
        """Helper to create or update an arrow centered at the mesh center."""

        # Remove previous arrow if it exists in the plotter
        if hasattr(self, arrow_attr_name) and getattr(self, arrow_attr_name) is not None:
            self.pv_widget.remove_actor(getattr(self, arrow_attr_name))

        # Create a new arrow mesh
        arrow_mesh = pv.Arrow(
            start=self.center,
            direction=direction_vec,
            scale=0.3,
            tip_resolution=30,
            shaft_resolution=20
        )

        # Add the new arrow to the scene and store the actor
        actor = self.pv_widget.add_mesh(
            arrow_mesh,
            color=color,
            name=arrow_attr_name,
            ambient=0.5,  # soft global fill light
            diffuse=0.8,  # normal Lambert lighting
            specular=0.2,  # a bit of shine

        )
        setattr(self, arrow_attr_name, actor)


class SliderLabels(QWidget):
    def __init__(self, times, parent=None, num_labels=5):
        super().__init__(parent)
        self.times = times
        self.num_labels = num_labels

    def update_config(self, times):
        self.times = times
        self.num_labels = min(5, len(times))

    def paintEvent(self, event):
        if len(self.times) == 0:
            return
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10))

        w = self.width()
        h = self.height()
        N = len(self.times)

        for i in range(self.num_labels):
            idx = int(i*(N-1)/(self.num_labels-1))
            x = int(i*(w-10)/(self.num_labels-1)) + 5
            painter.drawText(x - 15, h - 5, f"{self.times[idx]:.1f} h")

def quaternion_inverse(q):
    w, x, y, z = q
    norm_sq = w*w + x*x + y*y + z*z
    return np.array([w, -x, -y, -z]) / norm_sq