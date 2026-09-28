
"""
Bare Electrodynamic Tether - passive mode, closed-form current solver.

BETsMA Paper: https://www.sciencedirect.com/science/article/pii/S0094576522003113

TetherForceModel.py can call it every propagator timestep to get average current.

Partially bare tether: bare segment length xi_b + insulated segment xi_i, standard passive sub mode
R=We=0 , but using the analytical solution instead of a shooting method ODE integration : the approach 
BETsMA v2.0 itself uses internally, specifically
to avoid solving a boundary value problem at every timestep (Sanchez-Arriaga
et al. 2022, Appendix B.1, Eqs. B.2-B.10).

The only iterative step is a single 1-D brentq root find on phi_A (a handful of function evals, 
each just closed form algebra +
one lookup table evaluation of Fs) no ODE integration at all.

This module works entirely in normalized units (phi, xi, i), it has no
knowledge of physical units (meters, tesla, amps) or of orbit mechanics.
Converting physical inputs (tether geometry, local E-field, plasma density)
into normalized inputs, and converting the normalized average current back
into physical Amps, is TetherForceModel.py's job, not this module's, that
keeps this file testable standalone.


Guess phi_A (solve_phi_A), Walk along the bare part using Eq. 1 and Eq. 2 (bare_segment_state; the 
Fs table is a shortcut for this step), then Walk along the insulated part (a straight line, since 
no current is picked up there), Check whether you land on Phi_C at end C. If not, 
adjust the guess and repeat. Once it matches, compute i_av (average_current).

like BETsMA's own closed form, this neglects the small ion collection
current in the bit of bare wire between the crossing point and L_b (treated
as frozen, di/dxi=0, same as the insulated segment). See bet_passive_solver.py for the full
numerical model (with the ion branch) if that matters for validation.
"""

import numpy as np
from scipy.integrate import quad
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

'''
Fs(z), precomputed once, then lookup via cubic spline (both directions: Fs(z) and its inverse).
'''
def _fs_integrand(z):
    return np.sign(np.sinh(z)) * np.abs(np.sinh(z)) ** (1 / 3)


def _build_Fs_tables(zmax=15.0, n=4000):
    zgrid = np.linspace(0, zmax, n)
    Fs_vals = np.zeros_like(zgrid)
    for k in range(1, n):
        val, _ = quad(_fs_integrand, zgrid[k - 1], zgrid[k])
        Fs_vals[k] = Fs_vals[k - 1] + val
    return CubicSpline(zgrid, Fs_vals), CubicSpline(Fs_vals, zgrid)


Fs, Fs_inv = _build_Fs_tables()   # build once, reuse forever



# Closed-form bare segment relations (Eq. B.3-B.10)

def bare_segment_state(phi_A, xi_b):
    """Given phi_A = phi(0) and the bare length xi_b, return (phi_P, i_P,
    xi_AB) at the end of the bare segment (point P), using the closed form. xi_AB 
    distance from end A to point B, where the tether's voltage becomes 
    equal to the plasma's voltage (phi = 0)
    """
    if phi_A >= 1.0 - 1e-12:
        # Eq B.3-B.4
        if xi_b <= 4.0:
            phi_P = (1 - xi_b / 4) ** 4
            i_P = 1 - (1 - xi_b / 4) ** 3
        else:
            phi_P, i_P = 0.0, 1.0
        xi_AB = 4.0
        return phi_P, i_P, xi_AB

    base = 1 - phi_A ** 1.5                       # = 1 - phi_A^(3/2)
    v_c0 = np.arccosh(1.0 / np.sqrt(base))
    xi_AB = (4.0 / 3.0) * base ** (1.0 / 6.0) * Fs(v_c0)

    if xi_b <= xi_AB:
        # crossing not reached within the bare segment
        target_Fs = Fs(v_c0) - xi_b * 3.0 / (4.0 * base ** (1.0 / 6.0))
        v_b = Fs_inv(target_Fs)
        phi_P = base ** (2.0 / 3.0) * np.sinh(v_b) ** (4.0 / 3.0)
        i_P = 1 - np.sqrt(base) * np.cosh(v_b)
    else:
        # crossing at xi_AB, then frozen (Eq. B.9-B.10) out to xi_b
        i_B = 1 - np.sqrt(base) * np.cosh(0.0)     # = 1 - sqrt(base)
        i_P = i_B
        phi_P = (i_P - 1) * (xi_b - xi_AB)

    return phi_P, i_P, xi_AB


def solve_phi_A(xi_b, xi_i, phi_C):
    """For Standard sub mode in BETsMA (direct AEE connection, f_1(i_C)=0): solve for
    phi_A such that phi at the far end (after the insulated segment) equals
    phi_C.
    """
    def residual(phi_A):
        phi_P, i_P, _ = bare_segment_state(phi_A, xi_b)
        phi_Si = phi_P + (i_P - 1) * xi_i          # Eq. A.14, insulated segment
        return phi_Si - phi_C

    return brentq(residual, 1e-9, 1.0 - 1e-12, xtol=1e-12)


def average_current(phi_A, xi_b, xi_i, phi_C):
    """Current averaged over the whole active tether length (Eq. B.1),
    derived exactly from d(phi)/d(xi) = i(xi) - 1.

        i_av = 1 - (phi_A - phi_C) / xi_a,     xi_a = xi_b + xi_i

    This is the single number TetherForceModel needs each timestep; no
    call to a spatial profile function is required to get it.
    """
    xi_a = xi_b + xi_i
    return 1 - (phi_A - phi_C) / xi_a
