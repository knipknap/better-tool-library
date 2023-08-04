#!/usr/bin/python
import sys
from copy import deepcopy
from btl import Tool
from btl.params import IntParam
from btl.shape import builtin_shapes
from btl.toolmaterial import HSS, Carbide
from feeds import FeedCalc, Machine
from feeds.const import Operation
from feeds import material

def print_result(params):
    for name, param in sorted(params.items(), key=lambda x: x[0].lower()):
        print(f"{name: <18}: {param.to_string(decimals=10)}")

def run(operation):
    machine = Machine(max_power=2.2,
                      min_rpm=3000,
                      max_rpm=22000,
                      peak_torque_rpm=5020,
                      max_feed=5000)

    shape = builtin_shapes['endmill']
    shape.set_param(IntParam('Flutes'), 4)

    tool_material = Carbide
    endmill = Tool('Test tool', builtin_shapes['endmill'])
    endmill.set_stickout(35)
    endmill.set_material(tool_material)
    endmill.dump()

    mat = material.Aluminium6061
    mat.dump()

    fc = FeedCalc(machine, endmill, mat, operation=operation)
    #fc.doc.min = 8
    fc.update()
    print(f"Running {operation.name} operation on {fc.material.name} using a {tool_material.name} tool")

    results = []
    for i in range(100):
        fc.optimize()
        try:
            fc.validate()
        except AttributeError as e:
            err = str(e)
        else:
            err = None
        results.append((fc.get_error_distance(), err, deepcopy(fc.all_params())))

    error, msg, best = sorted(results, key=lambda x: x[0])[0]
    if msg:
        print(f"No valid result found. Error distance is {error}, with message: {msg}")
        print_result(best)
        sys.exit(1)

    print_result(best)
    endmill.pixmap.show_engagement(best['doc'].v, best['woc'].v)

if __name__ == '__main__':
    #import cProfile
    #cProfile.run("run(Operation.HSM)")
    run(Operation.HSM)
