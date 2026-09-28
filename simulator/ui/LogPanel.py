# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class LogPanel(QWidget):
    """
    A read-only log panel that displays simulation messages.
    """
    def __init__(self, parent=None):
        """
        Constructor for the log panel
        :param parent:
        """
        super().__init__(parent)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        # Read-only text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.text_area)

    def append_message(self, message: str) -> None:
        """
        Append a message to the log panel.
        :param message: The message to append
        :return:
        """
        current_datetime = QDateTime.currentDateTime()
        timestamp = current_datetime.toString("[yyyy-MM-dd hh:mm:ss] ")
        formatted_message = timestamp + message
        self.text_area.append(formatted_message)
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

    def clear(self) -> None:
        """
        Clear the log panel.
        :return:
        """
        self.text_area.clear()
