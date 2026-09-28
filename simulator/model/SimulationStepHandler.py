# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from jpype import JClass, JImplements, JOverride
import numpy as np

from simulator.Message import MessageType, Message
from simulator.model import Utilities
from simulator.model.DataStore import SpacecraftDataType, TimeDataType
from simulator.model.IlluminationCalculator import IlluminationCalculator

# JAVA orekit/hipparchus imports
OrekitFixedStepHandler = JClass("org.orekit.propagation.sampling.OrekitFixedStepHandler")
FastMath = JClass("org.hipparchus.util.FastMath")
FramesFactory = JClass("org.orekit.frames.FramesFactory")
Constants = JClass("org.orekit.utils.Constants")
CelestialBodyFactory = JClass("org.orekit.bodies.CelestialBodyFactory")
OneAxisEllipsoid = JClass("org.orekit.bodies.OneAxisEllipsoid")
IERSConventions = JClass("org.orekit.utils.IERSConventions")
TimeScalesFactory = JClass("org.orekit.time.TimeScalesFactory")
AbsoluteDate = JClass("org.orekit.time.AbsoluteDate")
EclipseDetector = JClass("org.orekit.propagation.events.EclipseDetector")
OccultationEngine = JClass("org.orekit.utils.OccultationEngine")
ReferenceEllipsoid = JClass("org.orekit.models.earth.ReferenceEllipsoid")
Binary64Field = JClass("org.hipparchus.util.Binary64Field")
FieldVector3D = JClass("org.hipparchus.geometry.euclidean.threed.FieldVector3D")
FieldOccultationAngles = JClass("org.orekit.utils.OccultationEngine.FieldOccultationAngles")
GeoMagneticFieldFactory = JClass("org.orekit.models.earth.GeoMagneticFieldFactory")
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")
TopocentricFrame = JClass("org.orekit.frames.TopocentricFrame")


def to_array(v, scale=1.0) -> np.array:
    """
    Utility function to convert a vector V to an array
    :param v:
    :param scale:
    :return:
    """
    return np.array([v.getX()*scale, v.getY()*scale, v.getZ()*scale])


@JImplements(OrekitFixedStepHandler)
class StepHandler:
    def __init__(self, cubesat):
        """
        Step Handler constructor for the CubeSat.  Most CubeSat
        models are delegated to the CubeSat step method, but some environment and other data
        collection done in this class
        :param cubesat:
        """
        self.step = None
        self.initial_date = None
        self.step_number = 0
        self.cubesat = cubesat


    @JOverride
    def init(self, s0, t, step):
        """
        Initialization method
        :param s0:
        :param t:
        :param step:
        :return:
        """
        self.step = step
        self.initial_date = s0.getDate()
        self.step_number = 0

    @JOverride
    def handleStep(self, current_state):
        """
        Method to handle the step, called back from the orbit propagator.  Update orbital info in data store
        and call cubesat step method to update cubesat model state
        :param current_state:
        :return:
        """
        try:
            if current_state.getDate().durationFrom(self.initial_date) > self.step:
                self.cubesat.step(current_state)

                self.step_number = self.step_number + 1
                if self.step_number % 50 == 0:
                    self.cubesat.status_queue.put(Message(MessageType.STATUS_SIMULATION_UPDATE, self.step_number))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

    @JOverride
    def finish(self, finalState):
        """
        Handles end of propagation, currently nothing to do
        :param finalState:
        :return:
        """
        self.cubesat.status_queue.put(Message(MessageType.STATUS_SIMULATION_UPDATE, self.step_number))


