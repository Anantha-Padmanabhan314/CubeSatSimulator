# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from enum import Enum


class MessageType(Enum):
    """
    The various message types supported between the PyVista/PySide6 and OreKIT processes
    """
    CMD_START_SIMULATION = "start simulation"
    CMD_SHUTDOWN_SIMULATOR = "shutdown simulator"
    STATUS_SIMULATION_COMPLETE = "simulation has completed"
    STATUS_SIMULATION_UPDATE = "simulation update"
    STATUS_SIMULATOR_SHUTDOWN = "simulator has shutdown"
    STATUS_LOG_MESSAGE = "log message"


class Message:
    """
    A message class for communicating between PyVista/PySide6 and OreKIT processes
    """
    def __init__(self, type: MessageType, data=None):
        """
        Constructor for an interprocess message
        :param type: the Message type
        :param data: data associated with the message
        """
        self.type = type
        self.data = data
