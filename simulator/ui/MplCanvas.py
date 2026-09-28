# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


class MplCanvas(FigureCanvas):
    """
    A wrapper class for a MatPlotLib canvas for displaying plotting data in the application
    """
    def __init__(self, width=6, height=4, dpi=100):
        """
        A constructor for the Canvas
        :param width: Canvas width
        :param height: Canvas height
        :param dpi: DPI for the canvas
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)


class MplPlotWidget(QWidget):
    """
    A QWidget that contains a Matplotlib canvas + toolbar with Zoom/Pan controls.
    """
    def __init__(self, width=6, height=4, dpi=100, parent=None):
        """
        Constructor for the plot widget
        :param width: The width of the plot widget
        :param height: The height of the plot widget
        :param dpi: The DPI for the plot widget
        :param parent: The parent panel
        """
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create canvas
        self.canvas = MplCanvas(width, height, dpi)
        layout.addWidget(self.canvas)

        # Add the toolbar for zoom, pan, save, etc.
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
