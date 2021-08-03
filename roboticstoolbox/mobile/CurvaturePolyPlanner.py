
import math
import scipy.integrate
import scipy.optimize
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple
from roboticstoolbox.mobile.Planner import Planner


def solvepath(poly, s_f, x0=[0, 0, 0], **kwargs):
    # poly is 4 coeffs of curvature polynomial
    # x0 is initial state of the vehicle
    def dotfunc(t, x, poly):
        theta = x[2]
        k = poly[0] * t ** 3 + poly[1] * t ** 2 + poly[2] * t + poly[3]
        return math.cos(theta), math.sin(theta), k

    sol = scipy.integrate.solve_ivp(dotfunc, [0, s_f], x0, args=(poly,), **kwargs)
    return sol.y

def costfunc(unknowns, start, goal):
    # final cost of path from start with params
    # p[0:4] is polynomial
    # p[4] is s_f
    path = solvepath(poly=unknowns[:4], s_f=unknowns[4], x0=start)
    e = np.linalg.norm(path[:, -1] - np.r_[goal])
    print(e, path[:, -1], np.r_[goal])
    return e
class CurvaturePolyPlanner(Planner):

    r"""
    Curvature polynomial planner

    :return: curvature polynomial path planner
    :rtype: CurvaturePolyPlanner instance

    ==================   ========================
    Feature              Capability
    ==================   ========================
    Plan                 Configuration space
    Obstacle avoidance   No
    Curvature            Continuous
    Motion               Forwards only
    ==================   ========================

    Creates a planner that finds the path between two configurations in the
    plane using forward motion only.  The path is a continuous cubic polynomial
    in curvature:

    .. math::

        \kappa(s) = \kappa_0 + as + b s^2 + c s^3, 0 \le s \le s_f 

    where :math:`\kappa_0` is the initial path curvature.  This is integrated along the path

    .. math::

        \theta(s) &= \theta_0 + \kappa_0 s + \frac{a}{2}s^2 + \frac{b}{3}s^3 + \frac{c}{4}s^4 \\
        x(s) &= x_0 + \int_0^s \cos \theta(t) dt \\
        y(s) &= y_0 + \int_0^s \sin \theta(t) dt

    where the initial configuration is :math:`(x_0, y_0, \theta_0)` and the final
    configuration is :math:`(x_{s_f}, y_{s_f}, \theta_{s_f})`.

    Numerical optimization is used to find the parameters path length
    :math:`s_f` and the polynomial coefficients :math:`(\kappa_0, a, b, c)`.

    :reference: Mobile Robotics, Cambridge 2013. Alonzo Kelly

    :seealso: :class:`Planner`
    """

    def __init__(self):
        super().__init__(ndims=3)

    def query(self, start, goal):
        r"""
        Find a curvature polynomial path

        :param start: start configuration :math:`(x, y, \theta)`
        :type start: array_like(3), optional
        :param goal: goal configuration :math:`(x, y, \theta)`
        :type goal: array_like(3), optional
        :return: path and status
        :rtype: ndarray(N,3), namedtuple

        The returned status value has elements:

        ==========  ===================================================
        Element     Description
        ==========  ===================================================
        ``length``  the length of the path, :math:`s_f`
        ``poly``    the polynomial coefficients :math:`(\kappa_0, a, b, c)`

        ==========  ===================================================
    
        :seealso: :meth:`Planner.query`
        """
        goal = np.r_[goal]
        start = np.r_[start]
        self._start = start
        self._goal = goal

        delta = goal[:2] - start[:2]
        d = np.linalg.norm(delta)
        # theta = math.atan2(delta[1], delta[0])
        sol = scipy.optimize.minimize(costfunc, [0, 0, 1, 0, d],
            bounds=[(None, None), (None, None), (None, None), (None, None), (d, None)],
            args=(start, goal,))

        path = solvepath(sol.x[:4], s_f=sol.x[4], x0=start, dense_output=True, max_step = 1e-2)

        status = namedtuple('CurvaturePolyStatus', ['length', 'poly'])(sol.x[4], sol.x[:4])

        return path.T, status

if __name__ == '__main__':
    from math import pi

    # start = (1, 1, pi/4)
    # goal = (-3, -3, -pi/4)
    start = (0, 0, -pi/4)
    goal = (1, 2, pi/4)

    # start = (0, 0, pi/2)
    # goal = (1, 0, pi/2)

    planner = CurvaturePolyPlanner()
    path, status = planner.query(start, goal)
    print('start', path[0,:])
    print('goal', path[-1, :])

    print(status)
    planner.plot(path, block=True)