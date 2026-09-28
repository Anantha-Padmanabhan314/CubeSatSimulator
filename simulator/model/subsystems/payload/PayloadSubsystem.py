# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.
import numpy as np
from jpype import JClass

from simulator.FrameVector import FrameVector
from simulator.model.Utilities import to_array
from simulator.model.subsystems.payload.PayloadConfig import PayloadConfigType, PayloadDataType
from simulator.model.subsystems.Subsystem import Subsystem

# JAVA orekit/hipparchus imports
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")


class PayloadSubsystem(Subsystem):

    
    def __init__(self, cubesat, payload_config):
        super().__init__("Payload", cubesat,
                         payload_config[PayloadConfigType.PAYLOAD_MASS],
                         payload_config[PayloadConfigType.PAYLOAD_POWER],
                         payload_config[PayloadConfigType.PAYLOAD_DATA_GENERATION_RATE])
        self.operational: bool = False
        self.tether_bare_len: float = payload_config[PayloadConfigType.TETHER_BARE_LEN]
        self.tether_insulated_len: float = payload_config[PayloadConfigType.TETHER_INSULATED_LEN]
        self.tether_conductivity: float = payload_config[PayloadConfigType.TETHER_CONDUCTIVITY]
        self.tether_cross_section_area: float = payload_config[PayloadConfigType.TETHER_CROSS_SECTION_AREA]
        self.tether_perimeter: float = payload_config[PayloadConfigType.TETHER_PERIMETER]
        self.aee_potential: float = payload_config[PayloadConfigType.TETHER_AEE_POTENTIAL]

    def capture(self) -> None:
        if self.operational:
            pass

    def update(self, dt: float, state) -> None:
        """
        Update method for the payload subsystem.

        The tether current is solved via TetherForceModel.compute_current(),
        called here with THIS method's own `state`, the propagator's
        integrator calls the same method independently, on its own adaptive
        step cadence, to compute the force actually applied to the orbit.
        Those two cadences are not the same (the integrator's internal steps
        can be far coarser than this method's reporting interval), so this
        calls compute_current() directly. The state is provided by the integrator. 
        Even if the cadence maybe coarser, the interpolation makes it smoother and the 
        state changes can be called by the payload subsystem to report relevant values 
        in a regular cadence.
        
        """
        force_model = self.cubesat.tether_force_model
        current = force_model.compute_current(state)[0] if force_model is not None else 0.0
        tether_len = self.tether_bare_len + self.tether_insulated_len

        tether_force = FrameVector(eci=(np.cross(self.cubesat.nadir.eci, self.cubesat.mag.eci) * current * tether_len), transformers=self.cubesat.transformer)
        self.cubesat.data_store.payload_data[PayloadDataType.TETHER_FORCE].append(tether_force)
        self.cubesat.data_store.payload_data[PayloadDataType.TETHER_CURRENT].append(current)
