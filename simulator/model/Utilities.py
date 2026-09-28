# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math
import numpy as np
from jpype import JClass

# JAVA orekit/hipparchus imports
DateTimeFormatter = JClass("java.time.format.DateTimeFormatter")
ZonedDateTime = JClass("java.time.ZonedDateTime")
TimeScalesFactory = JClass("org.orekit.time.TimeScalesFactory")
AbsoluteDate = JClass("org.orekit.time.AbsoluteDate")


def parse_date(utc_string: str) -> AbsoluteDate:
    """
    Utility method to parse a UTC String into a date
    :param utc_string:
    :return:
    """

    # Parse using Java's DateTimeFormatter
    formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssX")
    zdt = ZonedDateTime.parse(utc_string, formatter)

    # Convert to Orekit AbsoluteDate (UTC scale)
    utc = TimeScalesFactory.getUTC()
    return AbsoluteDate(zdt.getYear(), zdt.getMonthValue(), zdt.getDayOfMonth(),
                        zdt.getHour(), zdt.getMinute(), zdt.getSecond(), utc)


def to_array(v) -> np.array:
    """
    Utility function to convert to a numpy array
    :param v:
    :return:
    """
    return np.array([v.getX(), v.getY(), v.getZ()])


def omega_matrix(w):
    wx, wy, wz = w
    return np.array([
        [0, -wx, -wy, -wz],
        [wx, 0, wz, -wy],
        [wy, -wz, 0, wx],
        [wz, wy, -wx, 0]
    ])


def quat_to_rotmat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1-2*(x*x+z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1-2*(x*x+y*y)]
    ])


def quat_to_euler(q):
    """Convert quaternion to roll, pitch, yaw (radians)."""
    w, x, y, z = q / np.linalg.norm(q)
    roll = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
    pitch = math.asin(max(-1.0, min(1.0, 2*(w*y - z*x))))  # clamp
    yaw = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
    return np.array([roll, pitch, yaw])
