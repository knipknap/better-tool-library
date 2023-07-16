import os

__dir__ = os.path.dirname(__file__)
root = os.path.dirname(__dir__)
freecad_path = '/usr/lib/freecad/lib/' #FIXME
builtin_shape_dir = os.path.join(root, 'resources', 'shapes') #FIXME: store properly
builtin_shape_ext = '.fcstd'
builtin_shape_pattern = os.path.join(builtin_shape_dir, '*.fcstd')
