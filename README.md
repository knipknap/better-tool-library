# ToolDB

ToolDB is a command line tool and a Python module for managing tool libraries
and converting between them.

It support reading the following formats: FreeCAD, Camotics.
It supports writing the following formats: FreeCAD, Camotics, LinuxCNC.

## Examples

### Show the command line syntax

```
scripts/tooldb-manager.py --help
scripts/tooldb-manager.py -f camotics create --help
```

### Adding a tool to an existing library

```
scripts/tooldb-manager.py -f freecad fctooldir/ create tool endmill
```

### Converting from FreeCAD to Camotics tool table

```
scripts/tooldb-manager.py -f freecad fctooldir/ export -f camotics camoticstooldir/
```

### Converting from FreeCAD to LinuxCNC tool table

```
scripts/tooldb-manager.py -f freecad fctooldir/ export -f linuxcnc linuxcnc.tbl
```

### Converting from Camotics to FreeCAD tool table

```
scripts/tooldb-manager.py -f camotics camtest/ export -f freecad fctooldir/
```
