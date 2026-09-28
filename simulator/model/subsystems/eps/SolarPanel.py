import numpy as np
from numpy.linalg import norm
from scipy.spatial.transform import Rotation as R

from simulator.model.subsystems.eps.EpsConfig import EpsDataType


class SolarPanel:
    """
    Represents a single solar panel mounted on a CubeSat.

    Parameters
    ----------
    normal_body : array-like, shape (3,)
        Panel normal vector expressed in the spacecraft body frame.
        Does not need to be normalized.
    area : float
        Panel area in square meters.
    efficiency : float, optional
        Effective panel efficiency (default = 0.28)
    i_sc : float, optional
        Solar constant (W/m^2) at 1 AU (default = 1361 W/m^2)
    """

    def __init__(self, name: str, normal_body, area: float, efficiency: float = 0.28, i_sc: float = 1361.0):
        self.name=name
        self.normal_body = np.array(normal_body, dtype=float) / norm(normal_body)
        self.area = float(area)
        self.efficiency = float(efficiency)
        self.i_sc = float(i_sc)

    def power(self, q_body_to_inertial, sun_vector_inertial, illumination: float) -> float:
        """
        Compute power generation by this panel.

        Parameters
        ----------
        q_body_to_inertial : array-like, shape (4,)
            Quaternion representing body → inertial rotation (x, y, z, w format).
        sun_vector_inertial : array-like, shape (3,)
            Sun direction vector in inertial frame.
            Does not need to be normalized.
        illumination : float
            Fraction of full illumination (0 = total eclipse, 1 = full sun).

        Returns
        -------
        float
            Electrical power generated in watts.
        """

        # Normalize sun vector
        sun_vec_inertial = np.array(sun_vector_inertial, dtype=float)
        if norm(sun_vec_inertial) == 0:
            return 0.0
        sun_vec_inertial /= norm(sun_vec_inertial)

        # Rotate panel normal from body frame → inertial using quaternion
        r = R.from_quat(q_body_to_inertial)
        normal_inertial = r.apply(self.normal_body)

        # Cosine of incidence angle
        cos_theta = np.dot(normal_inertial, sun_vec_inertial)

        # Panel only generates power if sun is in front
        if cos_theta <= 0.0:
            return 0.0

        # Power model
        power = self.i_sc * self.area * self.efficiency * cos_theta * illumination
        return power
