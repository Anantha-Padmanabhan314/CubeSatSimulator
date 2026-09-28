# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math
from datetime import datetime, timezone
from queue import Queue

import numpy as np
from jpype import JClass

from simulator.FrameTransforms import FrameTransforms
from simulator.FrameVector import FrameVector
from simulator.Message import MessageType, Message
from simulator.model import SimulationStepHandler, Utilities
from simulator.model.AttitudePropagator import AttitudePropagator
from simulator.model.DataStore import DataStore, TimeDataType, SpacecraftDataType
from simulator.model.IlluminationCalculator import IlluminationCalculator
from simulator.model.ModelConfig import Config, ConfigType
from simulator.model.SimulationStepHandler import FastMath
from simulator.model.subsystems.ground.GroundSubsystem import GroundSubsystem
from simulator.model.subsystems.payload.TetherForceModel import TetherForceModel
from simulator.model.Utilities import parse_date
from simulator.model.subsystems.adcs.AdcsSubsystem import AdcsSubsystem
from simulator.model.subsystems.comms.CommsSubsystem import CommsSubsystem
from simulator.model.subsystems.payload.PayloadSubsystem import PayloadSubsystem
from simulator.model.subsystems.eps.EpsSubsystem import EpsSubsystem
from simulator.model.subsystems.structure.StructureSubsystem import StructureSubsystem

# JAVA orekit/hipparchus imports
OneAxisEllipsoid = JClass("org.orekit.bodies.OneAxisEllipsoid")
CelestialBodyFactory = JClass("org.orekit.bodies.CelestialBodyFactory")
IsotropicDrag = JClass("org.orekit.forces.drag.IsotropicDrag")
DragForce = JClass("org.orekit.forces.drag.DragForce")
FramesFactory = JClass("org.orekit.frames.FramesFactory")
TopocentricFrame = JClass("org.orekit.frames.TopocentricFrame")
GeoMagneticFieldFactory = JClass("org.orekit.models.earth.GeoMagneticFieldFactory")
HarrisPriester = JClass("org.orekit.models.earth.atmosphere.HarrisPriester")
OrbitType = JClass("org.orekit.orbits.OrbitType")
KeplerianOrbit = JClass("org.orekit.orbits.KeplerianOrbit")
Constants = JClass("org.orekit.utils.Constants")
IERSConventions = JClass("org.orekit.utils.IERSConventions")
NumericalPropagator = JClass("org.orekit.propagation.numerical.NumericalPropagator")
SpacecraftState = JClass("org.orekit.propagation.SpacecraftState")
DormandPrince853Integrator = JClass("org.hipparchus.ode.nonstiff.DormandPrince853Integrator")
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")
Rotation = JClass("org.hipparchus.geometry.euclidean.threed.Rotation")
HolmesFeatherstoneAttractionModel = JClass("org.orekit.forces.gravity.HolmesFeatherstoneAttractionModel")
GravityFieldFactory = JClass("org.orekit.forces.gravity.potential.GravityFieldFactory")
ZonedDateTime = JClass("java.time.ZonedDateTime")
PositionAngleType = JClass("org.orekit.orbits.PositionAngleType")
TimeScalesFactory = JClass("org.orekit.time.TimeScalesFactory")
AbsoluteDate = JClass("org.orekit.time.AbsoluteDate")


class CubeSat:
    """
    The CubeSat class is the top level class for the cubesat simulator.  It manages orbit propagation, attitude
    propagation and all subsystem models.  It also manages the process of running a cubesat simulation scenario
    """
    def __init__(self, status_queue: Queue, config: Config, drag_enabled: bool=True):
        """
        Constructor for the CubeSat class, the main class containing satellite
        functionality used during the simulation
        :param status_queue:
        :param config:
        :param drag_enabled:
        """
        self.name: str = config.name
        self.status_queue: Queue = status_queue

        self.date = None
        self.start_date = parse_date(config.start_date)
        self.last_step_date = None
        self.end_date = self.start_date.shiftedBy(config.duration * 3600 * 24)
        self.final_state = None

        self.itrs = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        self.orbit = None
        self.earth = OneAxisEllipsoid(
            Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
            Constants.WGS84_EARTH_FLATTENING,
            FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        )
        self.sun = CelestialBodyFactory.getSun()
        self.geoMagModel = GeoMagneticFieldFactory.getIGRF(2020)
        self.illumination_calculator = IlluminationCalculator()
        self.drag_enabled = drag_enabled
        self.transformer = None
        self.tether_force_model = None

        self.pos = None
        self.vel = None
        self.acc = None
        self.mag = None
        self.nadir = None
        self.sun_dir = None

        self.geo_point = None

        self.q_body_eci = np.zeros(4)
        self.q_body_lvlh = np.zeros(4)
        self.w_eci = np.zeros(3)
        self.rpy_body_eci = np.zeros(3)
        self.rpy_body_lvlh = np.zeros(3)

        self.illumination = 0
        self.eps = EpsSubsystem(self, config.eps_config)
        self.adcs = AdcsSubsystem(self, config.adcs_config)
        self.comms = CommsSubsystem(self, config.comms_config)
        self.structure = StructureSubsystem(self, config.structure_config)
        self.payload = PayloadSubsystem(self, config.payload_config)
        self.ground = GroundSubsystem(self, config.ground_config, config.stations)
        self.subsystems = [self.eps, self.adcs, self.comms, self.structure, self.payload, self.ground]
        self.mu = Constants.WGS84_EARTH_MU

        self.initial_orbit = KeplerianOrbit(
            config.spacecraft_config[ConfigType.ALT] * 1000 + 6378137.0,
            config.spacecraft_config[ConfigType.ECC],
            math.radians(config.spacecraft_config[ConfigType.INC]),
            math.radians(config.spacecraft_config[ConfigType.OMEGA]),
            math.radians(config.spacecraft_config[ConfigType.RAAN]),
            # The GUI field is the mean anomaly in degrees, so convert it like the other angles
            math.radians(config.spacecraft_config[ConfigType.LM]),
            PositionAngleType.MEAN,
            FramesFactory.getEME2000(),
            self.start_date,
            self.mu
        )
        inertia = np.diag([self.structure.Ixx, self.structure.Iyy, self.structure.Izz])
        q0_0 = config.spacecraft_config[ConfigType.Q0_0]
        q0_1 = config.spacecraft_config[ConfigType.Q0_1]
        q0_2 = config.spacecraft_config[ConfigType.Q0_2]
        q0_3 = config.spacecraft_config[ConfigType.Q0_3]
        w0_0 = config.spacecraft_config[ConfigType.W0_0]
        w0_1 = config.spacecraft_config[ConfigType.W0_1]
        w0_2 = config.spacecraft_config[ConfigType.W0_2]
        self.attitude_propagator = AttitudePropagator(inertia, [q0_0, q0_1, q0_2, q0_3], [w0_0, w0_1, w0_2])

        self.data_store = DataStore()

    def run_simulation(self, step_handler: SimulationStepHandler, step_size: float) -> None:
        """
        Method to run the simulation
        :param step_handler: a callback handler used by the propagator during orbit propagation
        :param step_size: the step size (in seconds) for the simulation (used for callback interval)
        :return:
        """
        try:
            # Convert initial orbit to Equinoctial type for stable propagation
            initial_equinoctial_orbit = OrbitType.EQUINOCTIAL.convertType(self.initial_orbit)

            min_step = 0.001
            max_step = 500.0
            scaling = 1.0  # scaling in meters for position tolerance
            abs_tol, rel_tol = NumericalPropagator.tolerances(scaling, initial_equinoctial_orbit, OrbitType.CARTESIAN)
            integrator = DormandPrince853Integrator(min_step, max_step, abs_tol, rel_tol)

            # --- Propagator Initialization ---
            propagator = NumericalPropagator(integrator)
            propagator.setOrbitType(OrbitType.EQUINOCTIAL)
            propagator.setInitialState(SpacecraftState(initial_equinoctial_orbit, self.get_mass()))

            GravityFieldFactory.addDefaultPotentialCoefficientsReaders()
            gravity_provider = GravityFieldFactory.getNormalizedProvider(20, 20)
            propagator.addForceModel(HolmesFeatherstoneAttractionModel(self.itrs, gravity_provider))
            if self.drag_enabled:
                propagator.addForceModel(self.get_drag_force_model())

            self.tether_force_model = TetherForceModel(
                self.payload.tether_bare_len,
                self.payload.tether_insulated_len,
                self.payload.tether_conductivity,
                self.payload.tether_cross_section_area,
                self.payload.tether_perimeter,
                self.payload.aee_potential,
                self.get_mass())
            propagator.addForceModel(self.tether_force_model)
            propagator.getMultiplexer().add(step_size, step_handler)

            self.status_queue.put(Message(MessageType.STATUS_LOG_MESSAGE,
                                          f"Simulation running for {self.name} from {get_date_time_str(self.start_date)} to {get_date_time_str(self.end_date)}..."))
            final_state = propagator.propagate(self.end_date) # Propagation 
            self.status_queue.put(Message(MessageType.STATUS_LOG_MESSAGE, f"Simulation complete for {self.name}"))
            self.status_queue.put(Message(MessageType.STATUS_SIMULATION_COMPLETE, self.data_store))
            self.data_store.export_single_csv("../output.csv")

            return final_state
        except Exception as e:
            import traceback
            self.status_queue.put(Message(MessageType.STATUS_LOG_MESSAGE, "Simulation error"))
            traceback.print_exc()
            raise

    def step(self, current_state) -> None:
        """
        Method to update the state of the CubeSat and associated subsystems
        :param current_state: the current state of the spacecraft (from orbit propagator)
        :return:
        """

        # Update spacecraft level properties
        self.date = current_state.getDate()
        dt = 0 if self.last_step_date is None else self.date.durationFrom(self.last_step_date)

        # ------------------------------
        # 1. Extract ECI POSITION & VELOCITY (Java -> NumPy)
        # ------------------------------
        pv_eci = current_state.getPVCoordinates()
        pv_ecef = current_state.getPVCoordinates(self.earth.getBodyFrame())
        pos_eci = Utilities.to_array(pv_eci.getPosition())
        vel_eci = Utilities.to_array(pv_eci.getVelocity())
        acc_eci = Utilities.to_array(pv_eci.getAcceleration())

        self.q_body_eci, self.w_eci, self.rpy_body_eci, self.q_body_lvlh, self.rpy_body_lvlh \
            = self.attitude_propagator.step(self.date, self.adcs.torque, dt, pv_ecef.getPosition(), pv_ecef.getVelocity())

        R_body_to_eci = np.array(
            Rotation(self.q_body_eci[0], self.q_body_eci[1], self.q_body_eci[2], self.q_body_eci[3], True).getMatrix(),
            dtype=float
        )
        eci = current_state.getFrame()
        ecef = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        R_eci_to_ecef = np.array(
            eci.getTransformTo(ecef, self.date).getRotation().getMatrix(),
            dtype=float
        )

        self.transformer = FrameTransforms(pos_eci, vel_eci, R_body_to_eci, R_eci_to_ecef)

        sun_pos = self.sun.getPVCoordinates(self.date, self.earth.getBodyFrame()).getPosition()
        sun_dir_eci = Utilities.to_array(sun_pos.subtract(pv_eci.getPosition()).normalize())

        self.orbit = current_state.getOrbit()

        self.pos = FrameVector(eci=pos_eci, transformers=self.transformer)
        self.vel = FrameVector(eci=vel_eci, transformers=self.transformer)
        self.acc = FrameVector(eci=acc_eci, transformers=self.transformer)
        # get_mag_field works in the Earth-fixed frame, so pass the ECEF position and store B as ECEF
        self.mag =FrameVector(ecef=Utilities.to_array(self.get_mag_field(pv_ecef.getPosition(), self.date)), transformers=self.transformer)
        self.nadir = FrameVector(eci=Utilities.to_array(pv_eci.getPosition().negate().normalize()), transformers=self.transformer)
        self.sun_dir = FrameVector(eci=sun_dir_eci, transformers=self.transformer)

        self.illumination = self.illumination_calculator.compute_fraction(current_state)
        self.geo_point = self.earth.transform(pv_eci.getPosition(), self.earth.getBodyFrame(), self.date)

        # Update the state of each subsystem
        for subsystem in self.subsystems:
            subsystem.update(dt, current_state)

        self.record_data()
        self.last_step_date = self.date

    def record_data(self):
        self.data_store.time_data[TimeDataType.ELAPSED_TIME].append( self.date.durationFrom(self.start_date) / 3600)
        self.data_store.time_data[TimeDataType.DATE].append(str(self.date))
        self.data_store.spacecraft_data[SpacecraftDataType.POSITION].append(self.pos)
        self.data_store.spacecraft_data[SpacecraftDataType.VELOCITY].append(self.vel)
        self.data_store.spacecraft_data[SpacecraftDataType.ACCELERATION].append(self.acc)
        # Eccentricity is dimensionless, so it is recorded as is (unlike inclination, which is an angle)
        self.data_store.spacecraft_data[SpacecraftDataType.ECCENTRICITY].append(self.orbit.getE())
        self.data_store.spacecraft_data[SpacecraftDataType.INCLINATION].append(FastMath.toDegrees(self.orbit.getI()))
        self.data_store.spacecraft_data[SpacecraftDataType.ALTITUDE].append(self.geo_point.getAltitude() / 1000)
        self.data_store.spacecraft_data[SpacecraftDataType.ILLUMINATION].append(self.illumination)
        self.data_store.spacecraft_data[SpacecraftDataType.NADIR_VECTOR].append(self.nadir)
        self.data_store.spacecraft_data[SpacecraftDataType.MAG_FIELD].append(self.mag)
        self.data_store.spacecraft_data[SpacecraftDataType.SUN_DIR].append(self.sun_dir)

    def get_drag_force_model(self):
        """
        Method to calculate and return the drag force based on the Harris-Priester atmosphere model
        :return:
        """
        atm_model = HarrisPriester(self.sun, self.earth)
        drag_model = IsotropicDrag(self.structure.drag_area, self.structure.drag_coef)
        drag_force = DragForce(atm_model, drag_model)
        return drag_force

    def get_mass(self) -> float:
        """
        Method for returning the mass of the CubeSat by summing up masses from all subsystems
        :return:
        """
        mass = 0.0
        for subsystem in self.subsystems:
            mass += subsystem.get_mass()
        return mass
    
    def get_mag_field(self, pos_itrs, t):
        """
        Calculates the magnetic field in ITRS frame at current cubesat position
        :param pos_itrs:
        :param t:
        :return:
        """
        geodetic = self.earth.transform(pos_itrs, self.itrs, t)
        alt_km = geodetic.getAltitude() / 1000.0
        field = self.geoMagModel.calculateField(geodetic.getLatitude(), geodetic.getLongitude(), alt_km)
        topo = TopocentricFrame(self.earth, geodetic, "local")

        # IGRF gives North, East, Down (NED)
        vec_ned = field.getFieldVector()
        Bn = float(vec_ned.getX())
        Be = float(vec_ned.getY())
        Bd = float(vec_ned.getZ())

        # Convert NED -> ENU for Orekit
        vec_enu = Vector3D(Be, Bn, -Bd)

        # Transform to ITRF
        transform = topo.getTransformTo(self.itrs, t)
        return transform.transformVector(vec_enu)

def get_date_time_str( date: AbsoluteDate ) -> str:
    utc = TimeScalesFactory.getUTC()
    start_dt = date.toDate(utc)
    py_start_dt = datetime.fromtimestamp(start_dt.getTime() / 1000, timezone.utc)
    return py_start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

