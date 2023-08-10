"""
Simplex Nelder-Mead Optimization (Amoeba Search)

The Amoeba algorithm is an iterative process that attempts to replace the
worst solution with a new and better solution at each step. The search
area (defined by a simplex) is said to move like a real “amoeba” when the
iteration results are graphed in action, which serves as the origin
of the method’s nickname. It is a type of pattern search that does not
require a gradient to find an optimal point. This makes the method very
easy to implement for a wide variety of numerical optimization tasks;
as such, it is often the first choice even among well-informed users.

https://chejunkie.com/knowledge-base/simplex-nelder-mead-optimization-amoeba-search/
https://en.wikipedia.org/wiki/Nelder%E2%80%93Mead_method
http://csg.sph.umich.edu/abecasis/class/815.20.pdf
"""
import math


def evaluate_simplex(dimension, simplex, fx, func):
    for i in range(dimension+1):
        fx[i] = func(simplex[i])

def simplex_extremes(dimension, fx, extremes):
    if fx[0] > fx[1]:
        extremes['hi'] = 0    # "Highest"
        extremes['lo'] = 1    # "Lowest"
        extremes['nhi'] = 1   # "Next-Highest"  (second-highest value)
    else:
        extremes['hi'] = 1
        extremes['lo'] = 0
        extremes['nhi'] = 0

    for i in range(2, dimension+1):
        if fx[i] <= fx[extremes['lo']]:
            extremes['lo'] = i
        elif fx[i] > fx[extremes['hi']]:
            extremes['nhi'] = extremes['hi']
            extremes['hi'] = i
        elif fx[i] > fx[extremes['nhi']]:
            extremes['nhi'] = i

def simplex_bearings(dimension, simplex, midpoint, line, hi):
    for j in range(dimension):
        midpoint[j] = 0

    for i in range(dimension+1):
        if i != hi:
            for j in range(dimension):
                midpoint[j] += simplex[i][j]

    for j in range(dimension):
        midpoint[j] /= dimension
        line[j] = simplex[hi][j] - midpoint[j]

def update_simplex(dimension, simplex, fx, idx, midpoint, line, scale, func):
    next_point = [midpoint[i] + scale * line[i] for i in range(dimension)]
    new_fx = func(next_point)

    if new_fx < fx[idx]:
        #print(next_point, "==>", new_fx)
        for i in range(dimension):
            simplex[idx][i] = next_point[i]
        fx[idx] = new_fx
        return True

    return False

def contract_simplex(dimension, simplex, fx, lo, func):
    for i in range(dimension+1):
        if i != lo:
            for j in range(dimension):
                simplex[i][j] = (simplex[lo][j] + simplex[i][j]) / 2
            fx[i] = func(simplex[i])

def check_tolerance(fmax, fmin, tolerance):
    delta = abs(fmax - fmin)
    accuracy = (abs(fmax) + abs(fmin)) * tolerance
    return delta < (accuracy + 0.00000001)

def amoeba(simplex, func, tolerance):
    """
    The simplex argument must contain the simplex (=a two-dimensional
    array) to be optimized.

    The func argument must contain a callback function that returns
    an error distance for the given point.
    """
    dimension = len(simplex[0])
    extremes = {}
    fx = [None]*(dimension+1)
    midpoint = [None]*dimension
    line = [None]*dimension

    evaluate_simplex(dimension, simplex, fx, func)

    for i in range(100):
        simplex_extremes(dimension, fx, extremes)
        simplex_bearings(dimension, simplex, midpoint, line, extremes["hi"])

        if check_tolerance(fx[extremes["hi"]], fx[extremes["lo"]], tolerance):
            # Minimum found
            break

        update_simplex(dimension, simplex, fx, extremes["hi"], midpoint, line, -1, func)

        if fx[extremes["hi"]] < fx[extremes["lo"]]:
            # Doubling
            update_simplex(dimension, simplex, fx, extremes["hi"], midpoint, line, -2, func)
        elif fx[extremes["hi"]] >= fx[extremes["nhi"]]:
            if not update_simplex(dimension, simplex, fx, extremes["hi"], midpoint, line, 0.5, func):
                # Contracting
                contract_simplex(dimension, simplex, fx, extremes["lo"], func)
            else:
                # Halving
                pass

    return simplex[extremes['lo']]
