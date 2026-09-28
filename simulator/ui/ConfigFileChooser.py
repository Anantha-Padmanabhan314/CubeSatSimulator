# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import pickle
from PySide6.QtWidgets import QFileDialog, QWidget, QMessageBox
import os
from typing import Optional

from simulator.model.ModelConfig import Config

class ConfigFileChooser:
    """
    A utility class to load and save Config objects using pickle via QFileDialog.
    """
    PICKLE_FILTER = "Pickle Config Files (*.pkl);;All Files (*.*)"
    # Define the home directory once
    HOME_DIR = os.path.expanduser('~')

    @staticmethod
    def load_config(parent: Optional[QWidget] = None) -> Optional[Config]:
        """
        Opens a file dialog to select a pickle file and loads a Config object from it.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            parent=parent,
            caption="Load Configuration File",
            dir=ConfigFileChooser.HOME_DIR,  # Set the default directory to the user's home
            filter=ConfigFileChooser.PICKLE_FILTER
        )

        if not file_path:
            return None  # User cancelled

        try:
            with open(file_path, 'rb') as file_handle:
                config_object = pickle.load(file_handle)
                if isinstance(config_object, Config):
                    QMessageBox.information(parent, "Success",
                                            f"Configuration loaded from {os.path.basename(file_path)}")
                    return config_object
                else:
                    QMessageBox.critical(parent, "Error", "File does not contain a valid Config object.")
                    return None
        except FileNotFoundError:
            QMessageBox.critical(parent, "Error", f"File not found: {file_path}")
            return None
        except pickle.UnpicklingError as e:
            QMessageBox.critical(parent, "Error", f"Could not read pickle file: {e}")
            return None
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def save_config(config_object: Config, parent: Optional[QWidget] = None) -> bool:
        """
        Opens a file dialog to choose a save location and saves the Config object as a pickle file.
        """
        # Suggest saving 'default_config.pkl' in the home directory
        default_save_path = os.path.join(ConfigFileChooser.HOME_DIR, "default_config.pkl")

        file_path, _ = QFileDialog.getSaveFileName(
            parent=parent,
            caption="Save Configuration File",
            dir=default_save_path,  # Use the default save path as the starting point
            filter=ConfigFileChooser.PICKLE_FILTER
        )

        if not file_path:
            return False  # User cancelled

        # Ensure .pkl extension if not provided
        if not file_path.lower().endswith('.pkl'):
            file_path += '.pkl'

        try:
            with open(file_path, 'wb') as file_handle:
                pickle.dump(config_object, file_handle)
            QMessageBox.information(parent, "Success", f"Configuration saved to {os.path.basename(file_path)}")
            return True
        except IOError as e:
            QMessageBox.critical(parent, "Error", f"Error saving file: {e}")
            return False