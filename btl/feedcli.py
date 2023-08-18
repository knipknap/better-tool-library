#!/usr/bin/python
import sys
from btl import Tool, Machine
from btl.shape import builtin_shapes
from btl.toolmaterial import HSS, Carbide
from btl.feeds import FeedCalc, material, operation
from btl.toolpixmap import EndmillPixmap, BullnosePixmap, ChamferPixmap, VBitPixmap

def print_result(params):
    for name, param in sorted(params.items(), key=lambda x: x[0].lower()):
        print(f"{name: <18}: {param.to_string(decimals=10)}")

def run(op):
    machine = Machine(max_power=2.2,
                      min_rpm=3000,
                      max_rpm=22000,
                      peak_torque_rpm=5020,
                      max_feed=5000)

    shape = builtin_shapes['endmill']
    shape.set_param('Flutes', 4)
    shape.set_param('Diameter', 3.175)
    shape.set_param('ShankDiameter', 3.175)
    shape.set_param('CuttingEdgeHeight', 15)

    tool_material = Carbide
    endmill = Tool('Test tool', shape)
    endmill.set_stickout(20)
    endmill.set_material(tool_material)
    endmill.dump()
    #return endmill.get_pixmap().show_engagement(0.1, 0.1)

    mat = material.Aluminium6061
    mat.dump()

    fc = FeedCalc(machine, endmill, mat, op=op)
    #fc.doc.min = 8
    print(f"Running {op.label} operation on {fc.material.name} using a {tool_material.name} tool")

    error, best = fc.start()
    if error is not None:
        print(f"No valid result found. Error message: {error}")
        print_result(best)
        sys.exit(1)

    print_result(best)
    #endmill.pixmap.show_engagement(best['doc'].v, best['woc'].v)

if __name__ == '__main__':
    #px = EndmillPixmap(20, 6, 5, 10)
    #px = BullnosePixmap(14, 8, 7, 5, 1.5)
    #px = VBitPixmap(14, 5, 10, 1.5, 45, .5)
    #px = ChamferPixmap(16, 6, 15, 2, 5)
    #px.show_engagement(0.1, 0.1)
    #import cProfile
    #cProfile.run("run(operation.HSM)")
    run(operation.HSM)
