# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from queue import Queue

from simulator.Message import MessageType, Message
from simulator.model.JvmUtilities import start_jvm, init_orekit

start_jvm()
init_orekit()

from simulator.model.CubeSat import CubeSat
from simulator.model.SimulationStepHandler import StepHandler


def run_simulator( config, msg_queue: Queue ):
        cubesat = CubeSat(msg_queue, config)
        cubesat.run_simulation(StepHandler(cubesat), config.step_size)
        msg_queue.put(Message(MessageType.STATUS_SIMULATION_COMPLETE))

