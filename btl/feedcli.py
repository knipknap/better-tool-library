import sys
from copy import deepcopy
from btl.toolmaterial import HSS, Carbide
from feeds import FeedCalc, Machine, Endmill
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
    endmill = Endmill(Carbide,
                      diameter=4,
                      shank_diameter=6,
                      stickout=15,
                      cutting_edge=10,
                      #corner_radius=1,
                      flutes=4)
    mat = material.Aluminium6061
    mat.dump()

    fc = FeedCalc(machine, endmill, mat, operation=operation)
    #fc.doc.min = 8
    fc.update()
    print(f"Running {operation.name} operation on {fc.material.name} using a {endmill.tool_material.name} tool")

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
    endmill.show_engagement(best['doc'].v, best['woc'].v)

if __name__ == '__main__':
    #import cProfile
    #cProfile.run("run(Operation.HSM)")
    run(Operation.HSM)
