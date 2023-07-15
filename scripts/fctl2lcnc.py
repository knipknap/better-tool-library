#!/usr/bin/python3
import os
import sys
import argparse
import json

def convert_unit(value):
    return value.rstrip(' m').replace(',', '.') if value else None

def parse_fctb_file(fctb_file):
    """Parse a .fctb file and return the tool data as a dictionary"""
    tool = {}
    with open(fctb_file, 'r') as f:
        fctb_data = json.load(f)
        params = fctb_data['parameter']
        diameter = params.get('ShankDiameter', params.get('ShaftDiameter', '0'))
        cutting_edge_length = params.get('CuttingEdgeHeight')

        tool['name'] = fctb_data['name']
        tool['diameter'] = convert_unit(diameter)
        tool['height'] = convert_unit(params['Length'])
        tool['corner_radius'] = convert_unit(params['Diameter'])
        tool['inner_radius'] = convert_unit(params['Diameter'])
        tool['cutting_edge_length'] = convert_unit(cutting_edge_length)
        tool['cutting_edge_angle'] = params.get('CuttingEdgeAngle', "90")

    return tool

def parse_fctl_file(filename):
    """
    Parse a FreeCAD .fctl file and yield a dict for each tool.
    """
    base_dir = os.path.dirname(os.path.dirname(filename))
    fctb_dir = os.path.join(base_dir, 'Bit')

    with open(filename, 'r') as fp:
        fctl_data = json.load(fp)

    # Iterate through each tool in the FreeCAD tool library
    for tool_elem in fctl_data['tools']:
        tool_path = tool_elem['path']
        fctb_path = os.path.join(fctb_dir, tool_path)
        tool_data = parse_fctb_file(fctb_path)
        tool_data['no'] = tool_elem['nr']
        yield tool_data

def parse_freecad_to_linuxcnc(fctl_filename, fp):
    """Parse a FreeCAD .fctl file and convert it to LinuxCNC tool.tbl file"""
    for tool in parse_fctl_file(fctl_filename):
        fp.write(f"T{tool['no']} P{tool['no']} D{tool['diameter']} ;{tool['name']}\n")

parser = argparse.ArgumentParser(
    prog='fctl2lcnc',
    description='Reads a FreeCAD tool library and exports all tools to a LinuxCNC .tbl file'
)

parser.add_argument('filename', help='the FreeCAD tool library file (.fctl)')
parser.add_argument('-o', '--output', help='an optional output file. default is stdout')

args = parser.parse_args()

if args.output:
    with open(args.output, 'w') as fp:
        parse_freecad_to_linuxcnc(args.filename, fp)
else:
    parse_freecad_to_linuxcnc(args.filename, sys.stdout)
