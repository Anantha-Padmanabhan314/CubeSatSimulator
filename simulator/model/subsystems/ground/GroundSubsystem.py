# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math
from jpype import JClass

from simulator.model.subsystems.Subsystem import Subsystem
from simulator.model.subsystems.ground.GroundConfig import GroundDataType, GroundConfigType

# JAVA orekit/hipparchus imports
TopocentricFrame = JClass("org.orekit.frames.TopocentricFrame")
OneAxisEllipsoid = JClass("org.orekit.bodies.OneAxisEllipsoid")
Constants = JClass("org.orekit.utils.Constants")
GeodeticPoint = JClass("org.orekit.bodies.GeodeticPoint")


class GroundSubsystem(Subsystem):
    """
    The Ground subsystem manages all contacts with selected ground stations.  In the future, may be included
    in RF link margin calculations etc...
    """
    def __init__(self, cubesat, ground_config, stations):
        """
        Constructor for the ground station subsystem model
        :param cubesat:
        :param ground_config:
        :param stations:
        """
        super().__init__("Ground", cubesat, 0, 0)

        self.ground_contact: bool = False
        self.earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS, Constants.WGS84_EARTH_FLATTENING, self.ITRF)
        self.station_points = {}
        self.station_frames = {}

        for station in stations:
            station_point = GeodeticPoint(math.radians(station['lat']), math.radians(station['lng']), station['altitude'])
            station_frame = TopocentricFrame(self.earth, station_point, station['name'])
            self.station_points[station['name']] = station_point
            self.station_frames[station['name']] = station_frame

    def update(self, dt: float, state) -> None:
        """
        Update method for the ground subsystem.
        :param dt: the duration of the timestep
        :param state: the state of the propagation
        :return:
        """
        ground_contact = False
        sat_pos_in_earth_frame = state.getPVCoordinates(self.earth.getBodyFrame()).getPosition()
        geodetic_point = self.earth.transform(sat_pos_in_earth_frame, self.earth.getBodyFrame(), state.getDate())
        for name in self.station_points.keys():
            station_point = self.station_points[name]
            station_frame = self.station_frames[name]
            stn_elevation_rad = station_frame.getElevation(sat_pos_in_earth_frame, self.earth.getBodyFrame(), state.getDate())
            stn_elevation_deg = math.degrees(stn_elevation_rad)
            ground_contact = ground_contact or (stn_elevation_deg >= 5)

        self.ground_contact = ground_contact
        self.cubesat.data_store.ground_data[GroundDataType.GROUND_VISIBLE].append(self.ground_contact)
        self.cubesat.data_store.ground_data[GroundDataType.SAT_NADIR_LAT].append(math.degrees(geodetic_point.getLatitude()))
        self.cubesat.data_store.ground_data[GroundDataType.SAT_NADIR_LONG].append(math.degrees(geodetic_point.getLongitude()))



