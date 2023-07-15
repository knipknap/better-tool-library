import os

freecad_path = '/usr/lib/freecad/lib/' #FIXME
builtin_shape_dir = os.path.join('resources', 'shapes') #FIXME: store properly
builtin_shape_ext = '.fcstd'
builtin_shape_pattern = os.path.join(builtin_shape_dir, '*.fcstd')
