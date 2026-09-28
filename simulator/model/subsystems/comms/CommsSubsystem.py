# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from simulator.model.subsystems.comms.CommsConfig import CommsConfigType, CommsDataType
from simulator.model.subsystems.Subsystem import Subsystem


class CommsSubsystem(Subsystem):
    """
    The COMMS subsystem manages all data collection, storage and transmission
    to the ground.  In future could also calculate RF link margin etc...
    """
    def __init__(self, cubesat, comms_config):
        """
        The COMMS subsystem constructor.
        :param cubesat: the parent cubesat
        :param comms_config: the COMMS sub system config data
        """
        super().__init__("Comms", cubesat, comms_config[CommsConfigType.COMMS_MASS], comms_config[CommsConfigType.COMMS_POWER])
        self.tx_datarate: float = comms_config[CommsConfigType.TX_DATARATE]
        self.data_buffer_bits: int = 0
        self.data_storage_capacity: int = comms_config[CommsConfigType.DATA_STORAGE_CAPACITY]
        self.transmitting_power = comms_config[CommsConfigType.COMMS_TX_POWER]

    def update(self, dt: float, state) -> None:
        """
        Update method for the COMMS subsystem.
        :param dt: the duration of the timestep
        :param state: the state of the propagation
        :return:
        """
        for subsystem in self.cubesat.subsystems:
            self.data_buffer_bits += subsystem.get_data_generation_rate() * dt

        if self.cubesat.ground.ground_contact:
            transmitted = min(self.tx_datarate * dt, self.data_buffer_bits)
            self.data_buffer_bits -= transmitted

        self.data_buffer_bits = min(self.data_buffer_bits, self.data_storage_capacity)
        self.cubesat.data_store.comms_data[CommsDataType.DATA_STORAGE].append(self.data_buffer_bits)

    def get_power_draw(self) -> float:
        if self.cubesat.ground.ground_contact:
            return self.transmitting_power
        return super().get_power_draw()
