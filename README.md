# Better Tool Library

Better Tool Library is a command line tool and a Python module for managing
tool libraries and converting between them.

It currently supports reading the following formats:
- FreeCAD
- Camotics

It supports writing the following formats:
- FreeCAD
- Camotics
- LinuxCNC

## Examples

### Show the command line syntax

```
btl-manager --help
btl-manager -f camotics create --help
```

### Print the whole library

```
btl-manager -f freecad fctooldir/ ls all
```

### Adding a tool to an existing library

```
btl-manager -f freecad fctooldir/ create tool endmill
```

### Converting from FreeCAD to Camotics tool table

```
btl-manager -f freecad fctooldir/ export -f camotics camoticstooldir/
```

### Converting from FreeCAD to LinuxCNC tool table

```
btl-manager -f freecad fctooldir/ export -f linuxcnc linuxcnc.tbl
```

### Converting from Camotics to FreeCAD tool table

```
btl-manager -f camotics camtest/ export -f freecad fctooldir/
```
