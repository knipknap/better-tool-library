## CLI tool

Better Tool Library also comes with a CLI tool.
After installation via setuptools (see above), you can use it as shown below.

### Show the command line syntax

```
btl --help
btl -f camotics create --help
```

### Print the whole library

```
btl fctooldir/ show all
```

(default for -f is freecad, so it can be omitted in that case)

### Adding a tool to an existing library

```
btl fctooldir/ create tool endmill
```

### Converting from FreeCAD to Camotics tool table

```
btl fctooldir/ export -f camotics camoticstooldir/
```

### Converting from FreeCAD to LinuxCNC tool table

```
btl fctooldir/ export -f linuxcnc linuxcnc.tbl
```

### Converting from Camotics to FreeCAD tool table

```
btl -f camotics camtest/ export -f freecad fctooldir/
```
