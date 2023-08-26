import math
import warnings
from scipy.optimize import minimize
import numpy as np
import random
from copy import deepcopy
from ..params import Param, IntParam, FloatParam
from . import operation

class InputParam(FloatParam):
    is_internal = False

class IntVar(IntParam):
    is_internal = False

class FloatVar(FloatParam):
    is_internal = False

class IntConst(IntParam):
    is_internal = True

class FloatConst(FloatParam):
    is_internal = True

class FeedCalc(object):
    def __init__(self, machine, endmill, material, op=operation.Slotting):
        self.machine = machine
        self.endmill = endmill
        self.material = material
        self.op = op

        # Perform some sanity checks.
        if op not in operation.operations:
            raise AttributeError(f"operation {op.label()} is not supported")

        min_speed, max_speed = endmill.get_speed_for_material(material, op)
        if not min_speed or not max_speed:
            attrname = 'min_speed' if not min_speed else 'max_speed'
            matname = material.name
            err = f'no {attrname} found for material {matname} and operation {op.label()}'
            raise AttributeError(err)

        # The calculator has three groups of properties:
        # 1. Input properties. These are doc, woc, chipload and speed
        #    and are never changed by our calculation.
        # 2. Working properties. These are updated by our calculations
        #    and later constraint-checked when the optimizer runs.
        # 3. Info properties. These are not used by the optimizer,
        #    but included in the result for reference and debugging.

        # A note about the max/limit values of parameters: The max value
        # should only ever be defined once here in this constructor.
        # The limit value may be changed during calculation, and it will
        # be reset to equal max before every iteration of the optimizer.
        # For setting reasonable "default limits" that depend only on
        # static parameters such as the tool diameter, set them in
        # Operation.prepare(), which will be called immediately after
        # the limits were reset.
        # This is to ensure that calculated values are clearly separated
        # from the original values and we won't be guessing whether
        # max was changed dynamically somewhere.

        # First group: Input properties
        # Attributes that the optimizer will populate and try to
        # optimize using a minimization algorithm (see .calculate()).
        # Note that the min/max values of these input parameters are
        # later used to calculate the relative increase of the parameters
        # during optimization.
        # If the range is small, the rate of change per iteration
        # is also small and may cause premature convergence.
        # Speed is the distance the outer edge of of the endmill travels
        # per minute.
        chipload = self.endmill.get_chipload_for_material(self.material)
        self.speed = InputParam(1, 999, 0, 'm/min')
        self.chipload = InputParam(0.0001, 10, 4, 'mm')
        self.woc = InputParam(chipload, 2500, 3, 'mm') # Width of cut (radial engagement)
        self.doc = InputParam(chipload, 2500, 3, 'mm') # Depth of cut (axial engagement)

        # Second group: Working properties
        # These also are the main attributes that a user may
        # want to get as a result. The calculator populates and
        # changes them according to the Operation.
        # As all properties, they also serve as "constraints" to
        # check whether the calculated values are valid.
        self.rpm = IntVar(machine.min_rpm.v, machine.max_rpm.v)
        min_feed = machine.min_feed.value('mm/min')
        max_feed = machine.max_feed.value('mm/min')
        self.feed = FloatVar(min_feed, max_feed, 1, 'mm/min') # The distance the tool travels each minute
        self.mrr = FloatVar(0.00001, 999, 2, 'cm³/min')   # material removal rate
        self.adjusted_chipload = FloatVar(0.0001, 12, 4, 'mm') # Should setup with same values as chipload
        self.power = FloatVar(0.00001, machine.max_power.value('kW'), 3, 'kW')
        self.torque = FloatVar(0.00001, machine.max_torque.value('Nm'), 2, 'Nm')
        self.deflection = FloatVar(0, 0.025, 3, 'mm') # actual deflection
        self.max_deflection = FloatVar(0, 0.05, 3, 'mm') # theoretical max deflection
        self.radial_force = FloatVar(0, 99999, 2, 'N') # Radial cutting force
        self.axial_force = FloatVar(0.01, 99999, 2, 'N') # Axial cutting force

        # Third group: Info properties
        # Properties NOT looked at by the optimizer. They are
        # derived from our parameter class only to make it easy
        # to display them with limits and error distance.
        # Their main purpose is providing info for debugging.
        self.available_torque = FloatConst(0.00001, 9999, 2, 'Nm')
        self.material_power_factor = FloatConst(0, 999, 8)
        self.speed_factor = FloatConst(0, 999, 2, v=1)
        self.chip_factor = FloatConst(0, 999, 2, v=1)
        self.feed_factor = FloatConst(0, 999, 2, v=1)
        self.radial_factor = FloatConst(0, 999, 2, v=1)
        self.axial_factor = FloatConst(0, 999, 2, v=1)
        self.engagement_angle = FloatConst(0, 180, 1, '°')
        self.effective_diameter = FloatConst(0.00001, 99999, 3, 'mm')
        self.overlap_area = FloatConst(0.00001, 999999, 3, 'mm²')
        self.bend_force_limit = FloatConst(0.00001, 9999, 2, 'N')
        self.twist_torque_limit = FloatConst(0.00001, 9999, 2, 'Nm')
        self.score = FloatConst(-self.mrr.max, 0, 2)

        # For easy access to all results.
        self.all_params = dict(p for p in self.__dict__.items()
                               if isinstance(p[1], Param))
        self.params = dict(p for p in self.all_params.items()
                           if not p[1].is_internal)

        self.op.prepare(self)

    def dump(self):
        params = sorted(self.all_params.items(), key=lambda x: x[0].lower())
        err = self.get_error()
        print(f"Scored {self.get_score():.4f}: {err}")
        for name, param in params:
            print(f"  {name: <18}: {param.to_string()}")

    def reshuffle(self):
        for param in self.params.values():
            if isinstance(param, InputParam):
                param.assign_random()

    def reset_limits(self):
        for param in self.all_params.values():
            param.reset_limit()
        self.op.prepare(self) # This-redefines some limits.

    def validate_params(self, tolerance=0.0001):
        for name, param in self.params.items():
            if param.get_error_distance() > tolerance:
                #print("FAILED", name, param.v, param.min, param.max, param.get_error_distance(), tolerance)
                raise AttributeError(f"Parameter {name} must be between {param.min} and {param.max}/{param.limit}, but is {param}")

    def validate(self):
        self.machine.validate()
        self.endmill.validate()
        self.validate_params()
        if self.endmill.shape.get_shank_diameter() > self.endmill.get_stickout():
            # This is due to ToolPixmap failing if the shape is wider than it is tall.
            raise AttributeError(f"Shank diameter larger than stickout is not supported.")
        if self.endmill.shape.get_diameter() > self.endmill.get_stickout():
            # This is due to ToolPixmap failing if the shape is wider than it is tall.
            raise AttributeError(f"Tool width larger than stickout is currently not supported.")
        if self.chipload.v > self.woc.min:
            raise AttributeError(f"Min WOC {self.woc.min} must be larger than Chipload {self.chipload}")
        if self.chipload.v > self.doc.min:
            raise AttributeError(f"Min DOC {self.doc.min} must be larger than Chipload {self.chipload}")

    def get_error(self):
        try:
            self.validate()
        except AttributeError as e:
            return str(e)
        return ''

    def is_valid(self):
        try:
            self.validate()
        except AttributeError:
            return False
        return True

    def update(self, reset_limits=True):
        if reset_limits:
            self.reset_limits()

        # Step 1:
        # Let the operation do the heavy lifting. This will adjust the
        # input DOC, WOC, speed, and chipload to optimize for the operation.
        # It will NOT guarantee that the result is valid - this will be
        # checked only by the constraint checker (minimization algorithm)
        # that aims to choose the best result out of many based on
        # an error distance, which takes the constraints into account.
        # See .optimize()
        self.op.optimize_cut(self, self.endmill, self.material)

        # Step 2:
        # Apply "classic" equations, in dependency order, assuming we have
        # selected DOC, WOC, SPEED, and CHIPLOAD:
        self.overlap_area.v = self.op.get_overlap(self.endmill, self.doc.v, self.woc.v)
        self.rpm.v = self.speed.v*1000 / (self.effective_diameter.v*math.pi)
        self.adjusted_chipload.v = self.chipload.v*self.feed_factor.v
        self.feed.v = self.adjusted_chipload.v*self.endmill.shape.get_flutes()*self.rpm.v
        self.mrr.v = self.feed.v*self.overlap_area.v/1000

        # Step 3:
        # Calculate power requirement for the resulting material removal rate.
        # The power factor is explained in material.py.
        # Note: Power calculation can probably be improved:
        #   https://www.machiningdoctor.com/calculators/machining-power/
        self.material_power_factor.v = self.material.power_factor
        self.power.v = self.mrr.v*self.material_power_factor.v   # power in KW
        #    (HP.v * OneHP * InchesPerFoot) / (2 * PI * RPM.v) = ft-lbf
        # =  (lb-ft/min * inchesperfoot)    / (2 * PI * RPM.v) = ft-lbf
        # =  lb-in/min                      / (2 * PI * RPM.v) = ft-lbf
        # =  lb-in/min                      / (2 * PI * RPM.v) = ft-lbf
        # =  lb-in/min                      / (2 * PI * RPM.v) * 1,35582= Nm
        # =  KW*44,253.73                   / (2 * PI * RPM.v) * 1,35582= Nm
        # =  KW*44,253.73*1.35582           / (2 * PI * RPM.v) = Nm
        # =  KW*60000                       / (2 * PI * RPM.v) = Nm
        self.torque.v = (self.power.v*60000)/(2*math.pi*self.rpm.v)

        # Step 4:
        # Calculate lead angle deflection for the given operation.
        self.radial_factor.v, self.axial_factor.v = self.op.get_lead_angle_deflection_factors(
            self.doc.v, self.woc.v, self.effective_diameter.v)

        # Force acting to bend the end mill.
        radial_force = (self.radial_factor.v*self.power.v*1000)/self.speed.v # kg m/s²
        self.radial_force.v = radial_force*60 # in Newton
        # Force acting to pull the end mill out of the tool holder (or the
        # workpiece off the table).
        axial_force = (self.axial_factor.v*self.power.v*1000)/self.speed.v # kg m/s²
        self.axial_force.v = axial_force*60 # in N

        # Get the deflection (multi-part bar)
        self.deflection.v = self.endmill.get_deflection(self.doc.v, self.radial_force.v)
        self.max_deflection.v = self.endmill.get_max_deflection(self.power.v/self.speed.v)

        # Step 5:
        # Calculate the force before permanently bending the end mill.
        self.bend_force_limit.v = self.endmill.get_bend_limit(self.doc.v)
        self.radial_force.set_limit(min(self.bend_force_limit.v, self.radial_force.limit))

        # Step 6:
        # How much torque is available at this RPM?
        self.available_torque.v = self.machine.get_torque_at_rpm(self.rpm.v)
        self.torque.set_limit(min(self.available_torque.v, self.torque.limit))

        # Step 7:
        # Maximum torque to shear the end mill
        self.twist_torque_limit.v = self.endmill.get_twist_limit()
        self.torque.set_limit(min(self.twist_torque_limit.v, self.torque.limit))
        self.available_torque.v = min(self.available_torque.v, self.torque.limit)

        # For information and debugging, include the current score
        # in our result.
        self.score.v = self.get_score()

    def get_error_distance(self):
        # Calculate the error distance of the result values from their limits
        d = 0
        for name, param in self.params.items():
            d += param.get_error_distance()
        return d

    def get_score(self):
        # Returns a positive value if there is an error, otherwise a
        # negative score where lower is better.
        if not self.is_valid():
            return self.get_error_distance()
        return -self.mrr.v # weighted. including doc to prioritize it over woc

    def _evaluate_point(self, point):
        self.speed.v = point[0]
        self.chipload.v = point[1]
        self.woc.v = point[2]
        self.doc.v = point[3]
        self.update()
        #print("EVAL", point, self.get_score(), self.get_error())
        return self.get_score()

    def optimize(self):
        # Try to find a valid initial point by assigning random values to all
        # parameters. But if that fails, continue trying to have the optimizer
        # figure it out anyway.
        for i in range(20):
            self.reset_limits()
            self.reshuffle()
            self.update(reset_limits=False)
            if self.is_valid():
                #print("Valid starting point found")
                break

        self.reset_limits()
        point = self.speed.v, self.chipload.v, self.woc.v, self.doc.v
        bounds = [(self.speed.min, self.speed.limit),
                  (self.chipload.min, self.chipload.limit),
                  (self.woc.min, self.woc.limit),
                  (self.doc.min, self.doc.limit)]
        np.set_printoptions(formatter={'float': lambda x: "{0:0.10f}".format(x)})
        with warnings.catch_warnings():  # ignore "out-of bounds" warning
            warnings.simplefilter("ignore", category=RuntimeWarning)
            result = minimize(self._evaluate_point,
                              point,
                              bounds=bounds,
                              method='SLSQP',  # evaluated fastest
                              #method='Powell',
                              #method='Nelder-Mead',
                              #method='TNC',
                              tol=0.001)

        # Load & recalculate the best result.
        self.speed.v, self.chipload.v, self.woc.v, self.doc.v = result.x
        #print("RESULT", result.x, result.success, result.message)
        self.update()

    def calculate(self, progress_cb=None, iterations=80):
        """
        Returns a list of results, where each result is a tuple:

          (error_distance, error, params)

        - error (str): An error message, if the result is invalid. None otherwse.
        - params (dict): The list of params, as stored in .all_params.
        """
        random.seed(1) # we don't want true randomness, rather reproducible results

        results = []
        for i in range(iterations):
            self.optimize()
            try:
                self.validate()
            except AttributeError as e:
                err = str(e)
            else:
                err = None
            params = deepcopy(self.all_params)
            result = err, params
            results.append(result)
            if progress_cb:
                progress_cb(100/iterations*i*0.01)

        return results

    def start(self, progress_cb=None, iterations=80):
        """
        Like calculate(), but only returns the best result.
        """
        results = self.calculate(progress_cb, iterations=iterations)
        results = sorted(results, key=lambda x: x[1]['score'].v)
        return results[0]
