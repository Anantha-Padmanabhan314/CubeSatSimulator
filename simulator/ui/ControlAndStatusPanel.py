# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.
from queue import Queue

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QLineEdit, QSizePolicy, QDateTimeEdit, QVBoxLayout
)
from PySide6.QtCore import Qt, QDate, QDateTime
from simulator.Message import MessageType, Message
from simulator.model.ModelConfig import Config
from simulator.model.subsystems.ground.GroundConfig import GroundConfigType
from simulator.ui.ConfigFileChooser import ConfigFileChooser


class ControlAndStatusPanel(QWidget):
    """
    A footer panel to show on the main display, that allows the simulation to be started, and provides
    some top-level config fields (e.g. mission name), and status data
    """
    def __init__(self, config: Config, cmd_queue: Queue, status_queue: Queue, parent):
        """
        Constructor for the ControlAndStatusPanel
        :param config: the CubeSat simulation configuration
        :param cmd_queue: The queue for submitting simulation command messages
        :param status_queue: The queue for receiving simulation status messages
        :param parent: The parent panel
        """
        super().__init__(parent)
        self.cmd_queue = cmd_queue
        self.status_queue = status_queue
        self.config = config
        self.parent = parent

        # Main horizontal layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(0)
        self.setLayout(main_layout)

        main_layout.addLayout(control_layout)

        self.play_button = QPushButton("▶️")
        self.load_button = QPushButton("📂")
        self.save_button = QPushButton("💾")

        for btn in (self.play_button, self.load_button, self.save_button):
            btn.setFixedSize(40, 40)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.play_button.clicked.connect(self.on_play_clicked)
        self.load_button.clicked.connect(self.on_load_clicked)
        self.save_button.clicked.connect(self.on_save_clicked)

        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.save_button)

        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Mission Name")
        self.name_field.setFixedWidth(200)
        self.name_field.setText(str(config.name))
        self.name_field.textChanged.connect(self.on_name_changed)

        qdt = QDateTime.fromString(config.start_date, "yyyy-MM-ddTHH:mm:ssZ")
        self.datetime_picker = QDateTimeEdit()
        self.datetime_picker.setCalendarPopup(True)
        self.datetime_picker.setDateTime(qdt)
        self.datetime_picker.setDisplayFormat("yyyy-MM-dd HH:mm:ss UTC")
        self.datetime_picker.setFixedWidth(200)  # Adjust width to fit date & time
        self.datetime_picker.dateTimeChanged.connect(self.on_datetime_changed)  # listener

        self.duration_field = QLineEdit()
        self.duration_field.setPlaceholderText("Duration (days)")
        self.duration_field.setFixedWidth(100)
        self.duration_field.setText(str(config.duration))
        self.duration_field.textChanged.connect(self.on_duration_changed)

        self.step_size_field = QLineEdit()
        self.step_size_field.setPlaceholderText("Step Size (s)")
        self.step_size_field.setFixedWidth(100)
        self.step_size_field.setText(str(config.step_size))
        self.step_size_field.textChanged.connect(self.on_step_size_changed)

        control_layout.addWidget(QLabel("Mission Name:"))
        control_layout.addWidget(self.name_field)
        control_layout.addWidget(QLabel("Start Date/Time:"))
        control_layout.addWidget(self.datetime_picker)
        control_layout.addWidget(QLabel("Duration (days):"))
        control_layout.addWidget(self.duration_field)
        control_layout.addWidget(QLabel("Step Size (s):"))
        control_layout.addWidget(self.step_size_field)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        control_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setMinimumWidth(400)
        main_layout.addWidget(self.status_label)

    def on_duration_changed(self, duration: str) -> None:
        self.config.duration = float(duration)

    def on_name_changed(self, name: str) -> None:
        self.config.name = name

    def on_step_size_changed(self, step_size: str) -> None:
        if( step_size!=''):
            self.config.step_size = float(step_size)

    def on_datetime_changed(self, qdatetime: QDateTime) -> None:
        utc_datetime = qdatetime.toUTC()
        utc_str = utc_datetime.toString("yyyy-MM-ddTHH:mm:ssZ")  # ISO 8601 UTC string
        self.config.start_date = utc_str

    def set_max_progress(self, max_progress) -> None:
        self.progress_bar.setRange(0, max_progress)
        self.progress_bar.setValue(0)

    def set_text(self, text: str) -> None:
        self.status_label.setText(text)

    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(value+1)

    def reset_progress(self) -> None:
        self.progress_bar.setValue(0)

    def on_play_clicked(self) -> None:
        self.play_button.setEnabled(False)
        self.duration_field.setEnabled(False)
        self.step_size_field.setEnabled(False)
        self.datetime_picker.setEnabled(False)
        self.set_max_progress(int(self.config.duration * 3600 * 24 / self.config.step_size))
        self.config.stations.clear()
        self.config.stations.extend(self.parent.ground_panel.stations_panel.selected_model._all)
        self.cmd_queue.put(Message(MessageType.CMD_START_SIMULATION, self.config))

    def on_load_clicked(self) -> None:
        loaded_config = ConfigFileChooser.load_config(parent=self)

        if loaded_config:
            self.config = loaded_config
            for station in self.parent.ground_panel.stations_panel.selected_model._all:
                if station['name'] not in self.config.ground_config[GroundConfigType.STATIONS]:
                    self.parent.ground_panel.stations_panel.available_view.move_station(
                        station['id'],
                        self.parent.ground_panel.stations_panel.selected_model,
                        self.parent.ground_panel.stations_panel.available_model,
                        station
                    )
            for station in self.parent.ground_panel.stations_panel.available_model._all:
                if station['name'] in self.config.ground_config[GroundConfigType.STATIONS]:
                    self.parent.ground_panel.stations_panel.selected_view.move_station(
                        station['id'],
                        self.parent.ground_panel.stations_panel.available_model,
                        self.parent.ground_panel.stations_panel.selected_model,
                        station
                    )

            self.parent.update_config(self.config)
            self.status_queue.put(Message(MessageType.STATUS_LOG_MESSAGE, "Successfully loaded spacecraft config"))
            self.duration_field.setText(str(self.config.duration))
            self.step_size_field.setText(str(self.config.step_size))
            qdt = QDateTime.fromString(self.config.start_date, "yyyy-MM-ddTHH:mm:ssZ")
            self.datetime_picker.setDateTime(qdt)
            self.name_field.setText(self.config.name)

    def on_save_clicked(self) -> None:
        self.config.ground_config[GroundConfigType.STATIONS].clear()
        for station in self.parent.ground_panel.stations_panel.selected_model._all:
            self.config.ground_config[GroundConfigType.STATIONS].add(station['name'])
        ConfigFileChooser.save_config(self.config, parent=self)
        self.status_queue.put(
            Message(MessageType.STATUS_LOG_MESSAGE, "Successfully saved spacecraft config"))
        self.status_queue.put(
            Message(MessageType.STATUS_LOG_MESSAGE, str(self.config)))

