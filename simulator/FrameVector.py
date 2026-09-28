import numpy as np


import numpy as np

class FrameVector:
    """
    Stores a point or vector expressed in multiple coordinate frames
    (ECI, ECEF, LVLH, Body). Uses only NumPy arrays internally → safe
    for multiprocessing.
    """

    def __init__(self, *,
                 eci=None,
                 ecef=None,
                 lvlh=None,
                 body=None,
                 transformers=None,
                 is_point=False):

        self._eci  = self._arr(eci)
        self._ecef = self._arr(ecef)
        self._lvlh = self._arr(lvlh)
        self._body = self._arr(body)

        self.is_point = is_point
        self.T = transformers   # must provide frame transform functions

    # --------------------
    # Utility
    # --------------------
    @staticmethod
    def _arr(x):
        if x is None:
            return None
        return np.asarray(x, dtype=float)

    # ============================================================
    # ECI
    # ============================================================
    @property
    def eci(self):
        if self._eci is None:
            if self._ecef is not None:
                self._eci = self.T.ecef_to_eci(self._ecef, self.is_point)
            elif self._lvlh is not None:
                self._eci = self.T.lvlh_to_eci(self._lvlh, self.is_point)
            elif self._body is not None:
                self._eci = self.T.body_to_eci(self._body, self.is_point)
        return self._eci

    @eci.setter
    def eci(self, v):
        self._eci = self._arr(v)

    # ============================================================
    # ECEF
    # ============================================================
    @property
    def ecef(self):
        if self._ecef is None:
            if self._eci is not None:
                self._ecef = self.T.eci_to_ecef(self._eci, self.is_point)
            elif self._lvlh is not None and hasattr(self.T, "lvlh_to_ecef"):
                self._ecef = self.T.lvlh_to_ecef(self._lvlh, self.is_point)
            elif self._body is not None and hasattr(self.T, "body_to_ecef"):
                self._ecef = self.T.body_to_ecef(self._body, self.is_point)
        return self._ecef

    @ecef.setter
    def ecef(self, v):
        self._ecef = self._arr(v)

    # ============================================================
    # LVLH
    # ============================================================
    @property
    def lvlh(self):
        if self._lvlh is None:
            if self._eci is not None:
                self._lvlh = self.T.eci_to_lvlh(self._eci, self.is_point)
            elif self._ecef is not None and hasattr(self.T, "ecef_to_lvlh"):
                self._lvlh = self.T.ecef_to_lvlh(self._ecef, self.is_point)
            elif self._body is not None and hasattr(self.T, "body_to_lvlh"):
                self._lvlh = self.T.body_to_lvlh(self._body, self.is_point)
        return self._lvlh

    @lvlh.setter
    def lvlh(self, v):
        self._lvlh = self._arr(v)

    # ============================================================
    # BODY (Mechanical-Built Frame)
    # ============================================================
    @property
    def body(self):
        if self._body is None:
            if self._eci is not None:
                self._body = self.T.eci_to_body(self._eci, self.is_point)
            elif self._lvlh is not None and hasattr(self.T, "lvlh_to_body"):
                self._body = self.T.lvlh_to_body(self._lvlh, self.is_point)
            elif self._ecef is not None and hasattr(self.T, "ecef_to_body"):
                self._body = self.T.ecef_to_body(self._ecef, self.is_point)
        return self._body

    @body.setter
    def body(self, v):
        self._body = self._arr(v)

    # ------------------------------------------------------------
    # Export
    # ------------------------------------------------------------
    def as_dict(self):
        return {
            "eci":  None if self._eci  is None else self.eci.tolist(),
            "ecef": None if self._ecef is None else self.ecef.tolist(),
            "lvlh": None if self._lvlh is None else self.lvlh.tolist(),
            "body": None if self._body is None else self.body.tolist(),
            "is_point": self.is_point,
        }

    def __repr__(self):
        return (
            f"FrameVector("
            f"ECI={self._eci}, "
            f"ECEF={self._ecef}, "
            f"LVLH={self._lvlh}, "
            f"BODY={self._body}, "
            f"is_point={self.is_point})"
        )
