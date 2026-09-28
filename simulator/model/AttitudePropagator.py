# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import math
from typing import Tuple
import numpy as np
from jpype import JClass

from simulator.model.Utilities import omega_matrix

# JAVA orekit/hipparchus imports
FramesFactory = JClass("org.orekit.frames.FramesFactory")
Transform = JClass("org.orekit.frames.Transform")
LocalOrbitalFrame = JClass("org.orekit.frames.LocalOrbitalFrame")
LOFType = JClass("org.orekit.frames.LOFType")
TopocentricFrame = JClass("org.orekit.frames.TopocentricFrame")
Vector3D = JClass("org.hipparchus.geometry.euclidean.threed.Vector3D")
OneAxisEllipsoid = JClass("org.orekit.bodies.OneAxisEllipsoid")
AbsoluteDate = JClass("org.orekit.time.AbsoluteDate")
PVCoordinates = JClass("org.orekit.utils.PVCoordinates")
AbsolutePVCoordinates = JClass("org.orekit.utils.AbsolutePVCoordinates")
IERSConventions = JClass("org.orekit.utils.IERSConventions")


class AttitudePropagator:
    """
    Simple attitude propagator with RK4 integration of rigid body motion given external torque
    """
    def __init__(self, inertia=np.diag([12,10,8]), q0=None, w0=None):
        self.I = np.array(inertia, float)
        self.Iinv = np.linalg.inv(self.I)
        self.q = np.array(q0 if q0 is not None else [1,0,0,0], float)
        self.q /= np.linalg.norm(self.q)
        self.w = np.array(w0 if w0 is not None else [0.0,0.0,0.0], float)

    def dynamics(self, q: np.ndarray, w: np.ndarray, tau: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        q_dot: np.ndarray = 0.5 * omega_matrix(w).dot(q)
        # noinspection PyUnreachableCode
        w_dot: np.ndarray = self.Iinv.dot(tau - np.cross(w, self.I.dot(w)))
        return q_dot, w_dot


    def step(self, date, tau, dt, position, velocity):
        """
        RK4 integration of rigid body attitude dynamics.
        Torque tau is assumed constant over dt.
        Returns updated quaternion, angular velocity, and roll-pitch-yaw (degrees).
        """
        def f(x, tau_body):
            """
            State derivative function for RK4
            x = [q0, q1, q2, q3, w_x, w_y, w_z]
            """
            q = x[:4]
            w = x[4:]

            # Angular velocity derivative in body frame
            w_dot = self.Iinv.dot(tau_body - np.cross(w, self.I.dot(w)))

            # Quaternion derivative
            q_dot = 0.5 * omega_matrix(w).dot(q)

            return np.concatenate([q_dot, w_dot])

        # State vector: quaternion + angular velocity
        x = np.concatenate([self.q, self.w])

        # RK4 coefficients
        k1 = f(x, tau)
        k2 = f(x + 0.5 * dt * k1, tau)
        k3 = f(x + 0.5 * dt * k2, tau)
        k4 = f(x + dt * k3, tau)

        # RK4 update
        x_next = x + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Extract new state
        q_next = x_next[:4]
        w_next = x_next[4:]

        # Normalize quaternion
        q_next /= np.linalg.norm(q_next)

        # Save updated state
        self.q, self.w = q_next, w_next

        # Compute roll, pitch, yaw (degrees)
        w_q, x_q, y_q, z_q = self.q
        roll = math.degrees(math.atan2(2*(w_q*x_q + y_q*z_q), 1 - 2*(x_q**2 + y_q**2)))
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2*(w_q*y_q - z_q*x_q)))))
        yaw = math.degrees(math.atan2(2*(w_q*z_q + x_q*y_q), 1 - 2*(y_q**2 + z_q**2)))
        rpy = np.array([roll, pitch, yaw])

        # Compute LVLH quaternion and RPY if needed
        q_body_lvlh, rpy_lvlh = body_to_lvlh_orekit(self.q, position, velocity, date)

        return self.q, self.w, rpy, q_body_lvlh, rpy_lvlh


def rotmat_from_quat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1-2*(x*x+z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1-2*(x*x+y*y)]
    ])


def rotmat_to_quat(R):
    tr = np.trace(R)
    if tr > 0:
        S = math.sqrt(tr+1.0)*2
        w = 0.25*S
        x = (R[2,1] - R[1,2]) / S
        y = (R[0,2] - R[2,0]) / S
        z = (R[1,0] - R[0,1]) / S
    elif (R[0,0] > R[1,1]) and (R[0,0] > R[2,2]):
        S = math.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])*2
        w = (R[2,1] - R[1,2]) / S
        x = 0.25*S
        y = (R[0,1] + R[1,0]) / S
        z = (R[0,2] + R[2,0]) / S
    elif R[1,1] > R[2,2]:
        S = math.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])*2
        w = (R[0,2] - R[2,0]) / S
        x = (R[0,1] + R[1,0]) / S
        y = 0.25*S
        z = (R[1,2] + R[2,1]) / S
    else:
        S = math.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])*2
        w = (R[1,0] - R[0,1]) / S
        x = (R[0,2] + R[2,0]) / S
        y = (R[1,2] + R[2,1]) / S
        z = 0.25*S
    return np.array([w, x, y, z])


def rotmat_to_rpy(R):
    sy = math.sqrt(R[0,0]**2 + R[1,0]**2)
    singular = sy < 1e-6
    if not singular:
        roll  = math.atan2(R[2,1], R[2,2])
        pitch = math.atan2(-R[2,0], sy)
        yaw   = math.atan2(R[1,0], R[0,0])
    else:
        roll  = math.atan2(-R[1,2], R[1,1])
        pitch = math.atan2(-R[2,0], sy)
        yaw   = 0.0
    return np.degrees([roll, pitch, yaw])


def body_to_lvlh_orekit(q_body_inertial, r_ecef, v_ecef, abs_date):
    """
    Convert body attitude (body→ECI) to LVLH frame given position/velocity in ECEF.
    Works fully within Orekit's Java-Python bridge (no subclassing required).
    """

    # --- Orekit frames ---
    itrf = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
    eme2000 = FramesFactory.getEME2000()

    # --- Convert to Orekit Vector3D ---
    r_vec = r_ecef
    v_vec = v_ecef

    # --- Create PV in ECEF ---
    pv_ecef = PVCoordinates(r_vec, v_vec)

    # --- Transform PV to ECI ---
    to_inertial = itrf.getTransformTo(eme2000, abs_date)
    pv_eci = to_inertial.transformPVCoordinates(pv_ecef)

    # --- Wrap as AbsolutePVCoordinates (implements PVCoordinatesProvider) ---
    abs_pv = AbsolutePVCoordinates(eme2000, abs_date, pv_eci)

    # --- Build LVLH frame ---
    lof = LocalOrbitalFrame(eme2000, LOFType.LVLH, abs_pv, "LVLH")

    # --- Rotation body→ECI ---
    R_eci_body = rotmat_from_quat(q_body_inertial)

    # --- Get rotation from LVLH→ECI ---
    R_eci_lvlh = np.array(lof.getTransformTo(eme2000, abs_date).getRotation().getMatrix())

    # --- Compose rotation LVLH←Body = (LVLH←ECI) * (ECI←Body)
    R_lvlh_body = R_eci_lvlh.T @ R_eci_body

    # --- Re-map LVLH axes into standard aerospace axes
    M = np.array([[1,0,0],
                  [0,0,1],
                  [0,1,0]])
    R_air = M @ R_lvlh_body @ M.T

    # --- Output quaternion + Euler ---
    q_body_lvlh = rotmat_to_quat(R_lvlh_body)
    rpy_lvlh = rotmat_to_rpy(R_air)
    return q_body_lvlh, rpy_lvlh
