import math
import numpy as np
import random
from . import const, operation
from .amoeba import amoeba
from .util import get_tool_engagement_angle, get_lead_angle_deflection_factor

random.seed(1) # we don't want true randomness, rather reproducible results

class Param:
    def __init__(self, decimals, min, max, metToImp, unit=None):
        self.decimals = decimals
        self.min = min
        self.max = max
        self.limit = max
        self.metToImp = metToImp
        self.unit = unit
        self.v = min

    def __str__(self):
        return str(self.v if self.v is not None else '')

    def assign_random(self):
        self.v = random.uniform(self.min, self.max)

    def set_limit(self, limit):
        self.limit = min(self.max, limit)

    def apply_limits(self):
        self.v = min(self.limit, self.max, self.v)
        self.v = max(self.min, self.v)

    def get_percent_of_max(self):
        return self.v/self.max

    def get_percent_of_limit(self):
        return self.v/min(self.max, self.limit)

    def get_error_distance(self):
        #if self.max < self.min:
        #    return self.min-self.max
        #elif self.limit < self.min:
        #    return self.min-self.limit
        if self.v > self.limit:
            return self.v-self.limit
        #elif self.v > self.max:
        #    return self.v-self.max
        elif self.v < self.min:
            return self.min-self.v
        return 0

    def get_error_distance_percent(self):
        dist = self.get_error_distance()
        diff = self.max-self.min
        return dist/diff if dist else 0

    def _format_value(self, value, decimals=None):
        fmt = "{{:.{}f}}".format(self.decimals if decimals is None else decimals)
        value = fmt.format(value) if isinstance(value, float) else str(value)
        if self.unit:
            if self.unit != '°':
                value += ' '
            value += self.unit
        return value

    def to_string(self, decimals=None):
        percent = self.get_percent_of_limit()*100
        value = self._format_value(self.v, decimals)
        min_value = self._format_value(self.min, decimals)
        max_value = self._format_value(self.max, decimals)
        limit = self._format_value(self.limit, decimals)
        return f"{value} ({percent:.0f}%) (min {min_value}, max {max_value}, limit {limit})"

class Const(Param):
    pass

class FeedCalc(object):
    def __init__(self, machine, endmill, material, op=operation.Slotting):
        self.machine = machine
        self.endmill = endmill
        self.material = material
        self.op = op

        if op not in operation.operations:
            raise AttributeError(f"operation {op.label} is not supported")

        # Constants, not looked at by the optimizer. They are
        # derived from our parameter class anyway, to make it easy
        # to display them with limits and error distance.
        self.available_torque = Const(2, 0, 9999, const.NMtoInLbs, 'Nm')
        self.feed_factor = Const(2, 0, 999, 1)
        self.engagement_angle = Const(0, 0, 180, 1, '°')
        self.bend_force_limit = Const(2, 0.01, 9999, const.NMtoInLbs, 'N')
        self.twist_torque_limit = Const(2, 0.01, 9999, const.NMtoInLbs, 'Nm')

        # Attributes that the optimizer will populate and try to
        # optimize using Simplex.
        # Speed is the distance the outer edge of of the endmill travels
        # per minute.
        min_speed, max_speed = endmill.get_speed_for_material(material, op)
        max_speed *= op.speed_multiplier

        if not min_speed or not max_speed:
            attrname = 'min_speed' if not min_speed else 'max_speed'
            matname = material.name
            err = f'no {attrname} found for material {matname} and operation {op.label}'
            raise AttributeError(err)

        self.speed = Param(0, 1, max_speed, const.SMMtoSFM, 'm/min')

        # Define the allowed chipload range.
        chipload = endmill.get_chipload_for_material(material)
        chipload *= op.chip_multiplier
        self.chipload = Param(4, 0.0001, chipload, const.mmToInch, 'mm')

        self.woc = Param(3, 0.01, endmill.shape.get_diameter(), const.mmToInch, 'mm') # Width of cut (radial engagement)
        self.doc = Param(3, 0.01, endmill.shape.get_cutting_edge(), const.mmToInch, 'mm') # Depth of cut (axial engagement)

        # Working attributes calculated. These also serve as "constraints" to
        # check whether the proposed attributes from Simplex may cause issues.
        self.rpm = Param(0, machine.min_rpm, machine.max_rpm, 1)
        self.feed = Param(1, machine.min_feed, machine.max_feed, const.mmToInch, 'mm/min') # The distance the tool travels each minute
        self.mrr = Param(2, 0.01, 999, const.cm3ToIn3, 'cm³/min')   # material removal rate
        self.adjusted_chipload = Param(4, 0.0001, chipload, const.mmToInch, 'mm') # Should setup with same values as chipload

        self.power = Param(2, 0.01, machine.max_power, const.KWToHP, 'kW')
        self.torque = Param(2, 0.01, machine.max_torque, const.NMtoInLbs, 'Nm')
        self.deflection = Param(2, 0, 0.025, const.mmToInch, 'mm') # actual deflection
        self.maxdeflection = Param(2, 0, 0.05, const.mmToInch, 'mm') # theoretical max deflection
        self.radial_force = Param(2, 0.01, 99999, const.KGtoLbs, 'N') # Radial cutting force
        self.axial_force = Param(2, 0.01, 99999, const.KGtoLbs, 'N') # Axial cutting force

    def all_params(self, names=None):
        if names is None:
            return dict(p for p in self.__dict__.items()
                        if isinstance(p[1], Param))
        return {n: getattr(self, n) for n in names}

    def params(self, names=None, include_const=False):
        return dict(p for p in self.all_params(names).items()
                    if not isinstance(p[1], Const))

    def dump(self):
        params = sorted(self.all_params().items(), key=lambda x: x[0].lower())
        for name, param in params:
            print(f"{name: <18}: {param.to_string()}")

    def reshuffle(self):
        for param in self.params().values():
            param.assign_random()

    def reset_limits(self):
        for param in self.params().values():
            param.limit = param.max

    def validate_params(self, names=None, tolerance=0.0001):
        for name, param in self.params(names).items():
            if param.get_error_distance() > tolerance:
                #print("FAILED", name, param.v, param.min, param.max, param.get_error_distance(), tolerance)
                raise AttributeError(f"Parameter {name} must be between {param.min} and {param.max}/{param.limit}, but is {param}")

    def validate(self):
        self.machine.validate()
        self.endmill.validate()
        self.validate_params()
        if self.chipload.v > self.woc.min:
            raise AttributeError(f"Min WOC {self.woc.min} must be larger than Chipload {self.chipload}")
        if self.chipload.v > self.doc.min:
            raise AttributeError(f"Min DOC {self.doc.min} must be larger than Chipload {self.chipload}")

    def is_valid(self):
        try:
            self.validate()
        except AttributeError:
            return False
        return True

    def update(self):
        self.reset_limits()

        """
        # TODO: Drilling
        # ------------------------
        # WOC / DOC -- irrelevant?
        # feed = chipload * rpm
        # MRR = area of drill * feed
        # Radial Force = 0 ?
        # No Helical Interpolation

        # TODO: Turning
        # ------------------------
        # DIAMETER = workpiece diameter
        # TEETH = 1
        # CHIPLOAD? = ?    radial depth?
        # DOC? = ?         irrelevant?
        # WOC? = ?         IPR?
        # MRR = (chipload * rpm) * DOC * Diameter
        # Radial Force = 0 ?
        # No Helical Interpolation

        # TODO: Helical Interpolation
        # ------------------------
        # - Adjust WOC and feed
        if self.op != operation.Slotting and self.op != operation.Drilling:
            woc, ipm = interpolate_helical(HELICAL.v, DIAMETER.v, WOC.v)
        """

        # Given the tool profile, get the effective diameter and MRR from the WOC and DOC.
        # Coordinates:
        #  (0,0) is centerline of tool, at the spindle nose.
        #  +X is to the right
        #  +Y is down (away from spindle)
        pixmap = self.endmill.get_pixmap()
        if self.op == operation.Drilling:
            overlap = math.pi * math.pow(self.endmill.shape.get_diameter()/2, 2)
            effective_diameter = self.endmill.shape.get_diameter()
        else:
            self.woc.v = self.endmill.shape.get_diameter() if self.op == operation.Slotting else self.woc.v
            overlap = pixmap.get_overlap_from_woc(self.doc.v, self.woc.v)
            effective_diameter = pixmap.get_effective_diameter_from_doc(self.doc.v)

        # When slotting/drilling, WOC is fixed.
        if self.op == operation.Slotting or self.op == operation.Drilling:
            self.woc.v = effective_diameter
            self.woc.set_limit(effective_diameter)

        # Tool Engagement Angle (straight shoulder along a straight path)
        #    TODO: Check that this works for slotting, helical, etc..
        if self.op == operation.Drilling:
            self.engagement_angle.v = 360
        else:
            self.engagement_angle.v = get_tool_engagement_angle(max(0, self.woc.v), effective_diameter)

        # Optimize chipload for the operation.
        speed_factor, chip_factor, self.feed_factor.v = \
            self.op.get_factors(self.doc.v,
                                max(0.00001, self.woc.v),
                                effective_diameter,
                                self.endmill.shape.get_corner_radius(),
                                self.endmill.shape.get_cutting_edge_angle()/2)

        speed_range = self.endmill.get_speed_for_material(self.material, operation.Milling)
        self.speed.set_limit(speed_range[1]*speed_factor)
        chipload = self.endmill.get_chipload_for_material(self.material)
        self.chipload.set_limit(chipload*chip_factor)

        # Adjust for lead angle deflection (unless drilling).
        if self.op == operation.Drilling:
            radialFactor = 0
            axialFactor = 1
        else:
            radialFactor, axialFactor = get_lead_angle_deflection_factor(self.doc.v,
                                                                         self.woc.v,
                                                                         effective_diameter)

        # The "classic" equations, in dependency order, assuming we have
        # selected DOC, WOC, SPEED, and CHIPLOAD:
        self.rpm.v = self.speed.v*1000 / (effective_diameter*math.pi)
        self.adjusted_chipload.v = self.chipload.v*self.feed_factor.v
        self.feed.v = self.adjusted_chipload.v*self.endmill.shape.get_flutes()*self.rpm.v
        self.mrr.v = self.feed.v*overlap/1000

        # Note: Power calculation can probably be improved:
        #   https://www.machiningdoctor.com/calculators/machining-power/
        self.power.v = self.mrr.v*self.material.power_factor
        self.torque.v = self.power.v*1000/(2*math.pi*self.rpm.v)*9548.8
        self.radial_force.v = (radialFactor*self.power.v*1000)/self.speed.v  # Force acting to bend the end mill.
        self.axial_force.v = (axialFactor*self.power.v*1000)/self.speed.v  # Force acting to pull the end mill out of the tool holder (or the workpiece off the table).

        # Get the deflection (multi-part bar)
        if self.op == operation.Drilling:
            self.deflection.v = 0
        else:
            self.deflection.v = self.endmill.get_deflection(self.doc.v, self.radial_force.v)
            self.maxdeflection.v = self.endmill.get_max_deflection(self.power.v/self.speed.v)

        # How much torque is available at this RPM?
        self.available_torque.v = self.machine.get_torque_at_rpm(self.rpm.v)
        self.torque.set_limit(min(self.available_torque.v, self.torque.limit))

        # Maximum Deflection to permanently bend the end mill
        self.bend_force_limit.v = self.endmill.get_bend_limit(self.doc.v)
        self.radial_force.set_limit(min(self.bend_force_limit.v, self.radial_force.limit))

        # Maximum Torque to shear the end mill
        self.twist_torque_limit.v = self.endmill.get_twist_limit()
        self.torque.set_limit(min(self.twist_torque_limit.v, self.torque.limit))
        self.available_torque.v = min(self.available_torque.v, self.torque.limit)

    def get_error_distance(self):
        # Calculate the error distance of the result values from their limits
        d = 0
        for name, param in self.params().items():
            if name == 'doc': # prioritize doc over woc
                d += param.get_error_distance()*2
            else:
                d += param.get_error_distance()
        return d

    def get_score(self):
        # Returns a positive value if there is an error, otherwise a
        # negative score where lower is better.
        if not self.is_valid():
            return self.get_error_distance()
        return -self.mrr.v - self.doc.v # weighted. including doc to prioritize it over woc

    def _make_simplex(self, dimension, points):
        simplex = []
        for i in range(dimension+1):
            simplex.append([])
            for j in range(dimension):
                simplex[i].append(points[j])

        simplex[0][0] += (self.speed.max-self.speed.min)/100
        simplex[1][1] += (self.chipload.max-self.chipload.min)/100
        simplex[2][2] += (self.woc.max-self.woc.min)/100
        simplex[3][3] += (self.doc.max-self.doc.min)/100

        return simplex

    def _jac(self, points):
        # Note that this function is unused for now; see note about
        # scipy.optimizer.minimize() below.
        new_speed    = points[0]+(self.speed.max-self.speed.min)/100
        new_chipload = points[1]+(self.chipload.max-self.chipload.min)/100
        new_woc      = points[2]+(self.woc.max-self.woc.min)/100
        new_doc      = points[3]+(self.doc.max-self.doc.min)/100
        #new_speed    = max(self.speed.min, min(self.speed.max, new_speed))
        #new_chipload = max(self.chipload.min, min(self.chipload.max, new_chipload))
        #new_woc      = max(self.woc.min, min(self.woc.max, new_woc))
        #new_doc      = max(self.doc.min, min(self.doc.max, new_doc))
        new_points = np.array((new_speed, new_chipload, new_woc, new_doc))
        return points-new_points   # scipy wants a gradient

    def _optimization_cb(self, point):
        self.speed.v = point[0]
        self.chipload.v = point[1]
        self.woc.v = point[2]
        self.doc.v = point[3]
        self.update()
        return self.get_score()

    def optimize(self):
        # Try to find a valid initial point by assigning random values to all
        # parameters. But if that fails, continue trying to have the optimizer
        # figure it out anyway.
        for i in range(20):
            self.reshuffle()
            self.update()
            if self.is_valid():
                #print("Valid starting point found")
                break

        point = [self.speed.v, self.chipload.v, self.woc.v, self.doc.v]
        simplex = self._make_simplex(4, point)
        amoeba(point, self._optimization_cb, 0.00001, simplex)
        self.speed.v, self.chipload.v, self.woc.v, self.doc.v = point
        self.update()

        # Note: I could not figure out how to use this scipy.optimizer.minimize()
        # in a similar manner as the Amoeba one here. The gradient returned by the
        # Jacobian function (_jac()) just doesn't seem to work the way I thought.
        """
        from scipy.optimize import minimize
        minimize(self._optimization_cb,
                 point,
                 jac=self._jac,
                 #hessp=self._make_simplex,
                 #callback=self.check_intermediate_result,
                 #constraints=[{'type': 'ineq', 'fun': lambda x: self.is_valid()}],
                 tol=0.00001,
                 method='CG',
                 #method='Nelder-Mead',
                 options={'disp': True, 'maxiter': 2000, 'adaptive': False})
        """
