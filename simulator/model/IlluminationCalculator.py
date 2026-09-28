# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math
from jpype import JClass

# JAVA orekit/hipparchus imports
FramesFactory = JClass("org.orekit.frames.FramesFactory")
CelestialBodyFactory = JClass("org.orekit.bodies.CelestialBodyFactory")
OneAxisEllipsoid = JClass("org.orekit.bodies.OneAxisEllipsoid")
IERSConventions = JClass("org.orekit.utils.IERSConventions")
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")


class IlluminationCalculator:

    def __init__(self):
        """
        Constructor for the IlluminationCalculator class, to calculate illumination of the
        spacecraft relative to the sun and moom
        """
        self.sun = CelestialBodyFactory.getSun()
        self.earth = OneAxisEllipsoid(
            6378137.0, 1.0 / 298.257223563,
            FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        )
        self.sun_radius = 6.957e8  # meters

    def compute_fraction(self, state):
        """
        Compute the fraction of the Sun visible from the spacecraft.
        Returns a float between 0 (full shadow) and 1 (full sunlight).
        """
        frame_itrs = self.earth.getBodyFrame()
        date = state.getDate()

        pos_sc = state.getPVCoordinates(frame_itrs).getPosition()
        pos_sun = self.sun.getPVCoordinates(date, frame_itrs).getPosition()
        pos_earth = Vector3D.ZERO  # Earth at origin in ITRF

        # Distances
        dist_sc_earth = pos_sc.distance(pos_earth)
        dist_sc_sun = pos_sc.distance(pos_sun)

        r_earth = self.earth.getEquatorialRadius()
        r_sun = self.sun_radius

        # Angular radii as seen from spacecraft
        alpha = math.asin(r_sun / dist_sc_sun)      # Sun apparent radius
        beta = math.asin(r_earth / dist_sc_earth)  # Earth apparent radius

        # Angle between Sun and Earth as seen from spacecraft
        v_se = pos_sun.subtract(pos_sc)  # vector from SC to Sun
        v_ee = pos_earth.subtract(pos_sc)  # vector from SC to Earth
        cos_theta = v_se.dotProduct(v_ee) / (v_se.getNorm() * v_ee.getNorm())
        cos_theta = max(-1.0, min(1.0, cos_theta))
        delta = math.acos(cos_theta)

        # Full sunlight
        if delta >= alpha + beta:
            return 1.0
        # Full umbra
        elif delta <= abs(beta - alpha):
            if beta > alpha:
                return 0.0  # Earth fully blocks Sun
            else:
                return 1.0  # Sun fully larger than Earth (rare)
        # Partial overlap (penumbra)
        else:
            # Geometric area of overlap of two circles
            x = (delta**2 + alpha**2 - beta**2) / (2 * delta)
            y = math.sqrt(max(alpha**2 - x**2, 0.0))
            a1 = alpha**2 * math.acos(x / alpha) - x * y
            y2 = math.sqrt(max(beta**2 - (delta - x)**2, 0.0))
            a2 = beta**2 * math.acos((delta - x) / beta) - (delta - x) * y2
            overlap_area = a1 + a2
            total_sun_area = math.pi * alpha**2
            fraction_visible = max(0.0, 1.0 - overlap_area / total_sun_area)
            return fraction_visible
