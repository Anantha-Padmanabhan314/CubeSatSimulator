# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math

from jpype import JImplements, JOverride, JClass

from simulator.model.subsystems.payload.BetClosedFormSolver import solve_phi_A, average_current
from simulator.model.subsystems.payload.PlasmaDensityModel import get_plasma_density

# JAVA orekit/hipparchus imports
FramesFactory = JClass("org.orekit.frames.FramesFactory")
Collections = JClass("java.util.Collections")
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")
TopocentricFrame = JClass("org.orekit.frames.TopocentricFrame")
IERSConventions = JClass("org.orekit.utils.IERSConventions")
OneAxisEllipsoid = JClass("org.orekit.bodies.OneAxisEllipsoid")
Constants = JClass("org.orekit.utils.Constants")
GeoMagneticFieldFactory = JClass("org.orekit.models.earth.GeoMagneticFieldFactory")

'''
Physical constants for the L* characteristic length formula for dimensional conversion.
'''

_M_E = 9.1093837015e-31       # electron mass, kg
_E_CHARGE = 1.602176634e-19   # elementary charge, C

'''
Below this, |E_m| is treated as numerically zero (tether momentarily aligned 
such that v_rel x B is approx perpendicular to nadir), L*/xi_b would blow up
(L* -> 0, xi_b -> inf) rather than just carry zero current, so this step's
tether force is skipped entirely instead of solving the singular case.
'''

_E_M_FLOOR = 1e-9


@JImplements("org.orekit.forces.ForceModel")
class TetherForceModel:

    def __init__(self, tether_bare_len, tether_insulated_len, tether_conductivity,
                 tether_cross_section_area, tether_perimeter, aee_potential, mass,
                 plasma_density_fn=get_plasma_density):
        self.tether_bare_len = tether_bare_len
        self.tether_insulated_len = tether_insulated_len
        self.tether_total_len = tether_bare_len + tether_insulated_len
        self.tether_conductivity = tether_conductivity
        self.tether_cross_section_area = tether_cross_section_area
        self.tether_perimeter = tether_perimeter
        self.aee_potential = aee_potential
        self.mass = mass
        self.plasma_density_fn = plasma_density_fn

        self.itrs = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        self.earth = OneAxisEllipsoid(
            Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
            Constants.WGS84_EARTH_FLATTENING,
            FramesFactory.getITRF(IERSConventions.IERS_2010, True))
        self.geoMagModel = GeoMagneticFieldFactory.getIGRF(2020)  # latest IGRF model
        '''
        Last-known values from whichever caller (the integrator, via
        acceleration(), or a subsystem calling compute_current() directly)
        last ran: handy for quick inspection/debugging.
        '''
        self.last_current = 0.0
        self.last_phi_A = None
        self.last_l_star = None

    @JOverride
    def addContribution(self, state, adder):
        acc = self.acceleration(state, None)
        if not isinstance(acc, Vector3D):
            acc = Vector3D(acc[0], acc[1], acc[2])
        adder.addNonKeplerianAcceleration(acc)
        return None

    @JOverride
    def dependsOnAttitudeRate(self):
        return False

    @JOverride
    def dependsOnPositionOnly(self):
        return True

    @JOverride
    def getParametersDrivers(self):
        return Collections.emptyList().stream()

    @JOverride
    def getFieldEventDetectors(self):
        return Collections.emptyList().stream()

    @JOverride
    def getEventDetectors(self):
        return Collections.emptyList().stream()

    def _geometry_and_field(self, state):
        """
        Frame transformation function shared by compute_current() and
        acceleration(): Gets the velocity, tether direction (nadir) and magnetic field from the orbit statet, 
        safe to call from anywhere at any cadence.
        """
        pv_itrf = state.getPVCoordinates(self.itrs)
        pos_itrf = pv_itrf.getPosition()
       
        vel_itrf = pv_itrf.getVelocity()
        nadir_itrs = pos_itrf.negate().normalize()

        geodetic = self.earth.transform(pos_itrf, self.itrs, state.getDate())
        alt_km = geodetic.getAltitude() / 1000.0
        field = self.geoMagModel.calculateField(geodetic.getLatitude(), geodetic.getLongitude(), alt_km)
        topo = TopocentricFrame(self.earth, geodetic, "local")

        # IGRF gives North, East, Down (NED)
        vec_ned = field.getFieldVector()
        # Convert NED to ENU for Orekit
        vec_enu = Vector3D(float(vec_ned.getY()), float(vec_ned.getX()), -float(vec_ned.getZ()))

        # Transform to ITRF
        transform = topo.getTransformTo(self.itrs, state.getDate())
        mag_itrs = transform.transformVector(vec_enu)

        return vel_itrf, nadir_itrs, mag_itrs, geodetic, alt_km

    def compute_current(self, state):
        """
        Solve for the tether's current at the given state. Both
        acceleration() (called by the integrator, on its own adaptive step
        cadence) and PayloadSubsystem.update() (called on the reporting
        cadence) call this directly with their own `state`, so telemetry
        reflects the actual instant it's tagged with rather than a value
        cached from whenever the integrator last happened to evaluate this
        force, those two cadences are not the same, and reading a cache
        written on one cadence from a caller on the other goes stale between
        real evaluations.

        Also updates self.last_current / last_phi_A / last_l_star, purely
        as a last known value convenience for inspection, not something
        another cadence should rely on for a live reading.

        :return: (current_amps, nadir_itrs, mag_itrs), the frame vectors
            are returned too so acceleration() doesn't repeat the transform.
        """
        vel_itrf, nadir_itrs, mag_itrs, geodetic, alt_km = self._geometry_and_field(state)

        e_m = float(Vector3D.crossProduct(vel_itrf, mag_itrs).dotProduct(nadir_itrs))

        if abs(e_m) < _E_M_FLOOR:
            
            '''
            Tether momentarily has no motional EMF along its length and therefore no current would flow; 
            skip the solve rather than divide by a near zero E_m.
            '''

            current, phi_a, l_star = 0.0, None, None
        else:
            n0 = self.plasma_density_fn(geodetic.getLatitude(), geodetic.getLongitude(), alt_km, state.getDate())

            # L* 
            l_star = (
                (2.0 * self.tether_cross_section_area / self.tether_perimeter) ** 2
                * (9.0 * math.pi ** 2 * _M_E * self.tether_conductivity ** 2 * abs(e_m))
                / (128.0 * _E_CHARGE ** 3 * n0 ** 2)
            ) ** (1.0 / 3.0)

            xi_b = self.tether_bare_len / l_star
            xi_i = self.tether_insulated_len / l_star
            phi_c = self.aee_potential / (abs(e_m) * l_star)

            try:
                phi_a = solve_phi_A(xi_b, xi_i, phi_c)
                i_av = average_current(phi_a, xi_b, xi_i, phi_c)
                if i_av < 0.0:
                    #Treat as no current rather than propagate an unphysical value into the force.
                    current = 0.0
                else:
                    
                    current = i_av * abs(e_m) * self.tether_conductivity * self.tether_cross_section_area
                    if e_m < 0.0:
                        current = -current
            except ValueError:
                '''
                 brentq failed to bracket a root for this instant's (xi_b,
                xi_i, phi_c), treat as no current rather than crash the
                whole propagation over one bad timestep.
                '''
                
                phi_a, current = None, 0.0

        self.last_current = current
        self.last_phi_A = phi_a
        self.last_l_star = l_star
        return current, nadir_itrs, mag_itrs

    @JOverride
    def acceleration(self, state, parameters):
        current, nadir_itrs, mag_itrs = self.compute_current(state)

        tether_force_itrs = (
            Vector3D.crossProduct(nadir_itrs, mag_itrs)
            .scalarMultiply(current)
            .scalarMultiply(self.tether_total_len)
        )

        acc_itrf = tether_force_itrs.scalarMultiply(1 / self.mass)

        # Must convert back to the propagation frame
        transform = state.getFrame().getTransformTo(self.itrs, state.getDate())
        acc_in_inertial = transform.getInverse().transformVector(acc_itrf)
        return acc_in_inertial

    @JOverride
    def init(self, state, target):
        return None
