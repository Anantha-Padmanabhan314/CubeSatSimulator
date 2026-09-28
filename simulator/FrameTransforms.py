import numpy as np

def normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


class FrameTransforms:
    """
    Transform vectors or points between:
        ECI, ECEF, LVLH, BODY
    using a unified method signature:
        transform(vec, is_point)
    """

    def __init__(self, pos_eci, vel_eci, R_body_to_eci, R_eci_to_ecef):

        # Spacecraft state (ECI)
        self.pos_eci = np.asarray(pos_eci)
        self.vel_eci = np.asarray(vel_eci)

        # Body rotation
        self.R_body_to_eci = np.asarray(R_body_to_eci)
        self.R_eci_to_body = self.R_body_to_eci.T

        # Earth rotation
        self.R_eci_to_ecef = np.asarray(R_eci_to_ecef)
        self.R_ecef_to_eci = self.R_eci_to_ecef.T

        # LVLH rotation
        self.R_eci_to_lvlh = self._compute_eci_to_lvlh(self.pos_eci, self.vel_eci)
        self.R_lvlh_to_eci = self.R_eci_to_lvlh.T

    # ------------------------------------------------------------
    # Build LVLH DCM
    # ------------------------------------------------------------

    def _compute_eci_to_lvlh(self, r_eci, v_eci):
        r = np.asarray(r_eci)
        v = np.asarray(v_eci)

        eR = -normalize(r)
        h = np.cross(r, v)
        eW = normalize(h)
        eS = np.cross(eW, eR)

        return np.vstack([eR, eS, eW])

    # ------------------------------------------------------------
    # Unified transform interfaces
    # ------------------------------------------------------------

    # ----- ECI <-> ECEF -----

    def eci_to_ecef(self, x, is_point):
        if is_point:
            return self.R_eci_to_ecef @ x
        else:
            return self.R_eci_to_ecef @ x

    def ecef_to_eci(self, x, is_point):
        if is_point:
            return self.R_ecef_to_eci @ x
        else:
            return self.R_ecef_to_eci @ x

    # ----- ECI <-> LVLH -----

    def eci_to_lvlh(self, x, is_point):
        if is_point:
            rel = x - self.pos_eci
            return self.R_eci_to_lvlh @ rel
        else:
            return self.R_eci_to_lvlh @ x

    def lvlh_to_eci(self, x, is_point):
        if is_point:
            return self.pos_eci + self.R_lvlh_to_eci @ x
        else:
            return self.R_lvlh_to_eci @ x

    # ----- ECI <-> BODY -----

    def eci_to_body(self, x, is_point):
        if is_point:
            rel = x - self.pos_eci
            return self.R_eci_to_body @ rel
        else:
            return self.R_eci_to_body @ x

    def body_to_eci(self, x, is_point):
        if is_point:
            return self.pos_eci + self.R_body_to_eci @ x
        else:
            return self.R_body_to_eci @ x
