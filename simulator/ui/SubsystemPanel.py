# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QTabWidget, QLineEdit, QFormLayout, QTextEdit, QVBoxLayout
)

from simulator.FrameVector import FrameVector
from simulator.ui.MplCanvas import MplPlotWidget
from simulator.ui.NotesPanel import NotesPanel


class SubsystemPanel(QWidget):
    """
    A general-purpose subsystem panel, can be used by any subsystem that doesn't have special-purpose
    visualization requirements.
    """
    def __init__(self, config_types, data_types, config, parent=None):
        """
        Constructor for the general purpose subsystem panel
        :param config_types: The set of configuration types relevant for the subsystem, used to create editor fields
        :param data_types: The set of data types relevant for the subsystem, used to generate plots of subsystem behaviour
        :param config: The current configuration of the subsystem
        :param parent: The parent panel
        """
        super().__init__(parent)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        self.plots = {}
        self.fields = {}
        self.config = config
        self.data_types = data_types

        # ------------------ Left Side: Plot Tabs ------------------
        plot_tabs = QTabWidget()
        main_layout.addWidget(plot_tabs, stretch=2)  # give more space to plots

        for data_type in self.data_types:
            plot = MplPlotWidget()
            plot.canvas.axes.set_title(data_type.value)
            plot_tabs.addTab(plot, data_type.value)
            self.plots[data_type] = plot

        # ------------------ Right Side: Config + Notes Tabs ------------------
        right_tabs = QTabWidget()
        main_layout.addWidget(right_tabs, stretch=1)

        # --- Config Tab ---
        config_widget = QWidget()
        config_layout = QFormLayout(config_widget)

        for config_item in config_types:
            field = QLineEdit()
            field.setMinimumWidth(150)
            field.setText(str(self.config[config_item]))
            field.textChanged.connect(lambda new_text, item=config_item: self.on_field_changed(item, new_text))

            config_layout.addRow(config_item.value, field)
            self.fields[config_item] = field

        right_tabs.addTab(config_widget, "Config")

        # --- Notes Tab ---
        self.notes_widget = NotesPanel(config, self)
        right_tabs.addTab(self.notes_widget, "Notes")

    def update_config(self, config) -> None:
        """
        A method to update the configuration shown in the subsystem panel
        :param config:
        :return:
        """
        self.config = config
        for config_item, field in self.fields.items():
            field.setText(str(self.config[config_item]))
        self.notes_widget.update_config(config)

    @Slot(object, str)
    def on_field_changed(self, item_identifier, new_text) -> None:
        """
        Method to capture a field-change event, to update the associated subsystem config parameter
        :param item_identifier: identifier for the field
        :param new_text: The new data supplied by the user to use in updating the config
        :return:
        """
        try:
            if new_text:
                self.config[item_identifier] = float(new_text)
        except ValueError:
            print(f"Invalid float value entered for {item_identifier.value}: {new_text}")

    def update_plots(self, times, data) -> None:
        """
        Method to update the plots contained in the subsystem panel
        :param times: The times related to the data to plot
        :param data: The subsystem-level data to plot
        :return:
        """
        for data_type in self.data_types:
            canvas = self.plots[data_type].canvas

            # Clear old lines
            for line in canvas.axes.lines:
                line.remove()

            series = data[data_type]

            if series:
                # Extract `.eci` for FrameVector, keep numeric values unchanged
                cleaned = [
                    (v.eci if isinstance(v, FrameVector) else v)
                    for v in series
                ]

                canvas.axes.plot(times, cleaned)
                canvas.draw()