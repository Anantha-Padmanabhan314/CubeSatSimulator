# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import markdown
from PySide6.QtWidgets import QTextEdit, QTextBrowser, QTabWidget, QVBoxLayout, QWidget

from simulator.model.ModelConfig import NotesType


class NotesPanel(QWidget):
    """
    A general notes panel for notes related to the cubesat
    """
    def __init__(self, config, parent=None):
        """
        A constructor for the notes panel
        :param config:
        :param parent:
        """
        super().__init__()
        self.config = config

        # Main layout
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- Markdown Edit Tab ---
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("# Start typing Markdown here...")
        if NotesType.NOTES in config:
            self.editor.setText(self.config[NotesType.NOTES])
        self.editor.textChanged.connect(self.update)

        # --- Preview Tab ---
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        # Add tabs
        self.tabs.addTab(self.preview, "Notes")
        self.tabs.addTab(self.editor, "Source")

        self.update()

    def update_config(self, config) -> None:
        """
        Method to update the notes contained in this panel (e.g. when new config is loaded)
        :param config: the new config
        :return:
        """
        self.config = config
        if NotesType.NOTES in config:
            self.editor.setText(self.config[NotesType.NOTES])
        self.update()

    def update(self) -> None:
        md_text = self.editor.toPlainText()
        self.config[NotesType.NOTES] = self.editor.toPlainText()
        html = markdown.markdown(md_text, extensions=["extra", "tables", "fenced_code"])
        self.preview.setHtml(html)