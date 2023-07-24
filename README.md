# Better Tool Library (BTL)

Better Tool Library (BTL) is a FreeCAD addon (plugin) that replaces the built-in tool library
for the Path workbench.
It also provides a standalone tool if you want to use your library outside of FreeCAD.

> **Warning**
> If you decide to switch back from BTL to the FreeCAD internal tool library,
> you may lose any extra information that was entered using Better Tool Library,
> like tool notes and hardware.

> **Warning**
> I advise you make a backup of your tool library. I guarantee for nothing,
> there may be bugs.


## Feature Comparison

| Feature                                    | Better Tool Library   | FreeCAD internal library  |
| :--                                        |        :--:           |          :--:             |
| Modern UI                                  | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides a shape browser                   | ![X](media/check.svg) | ![-](media/no.svg)        |
| Tool search                                | ![X](media/check.svg) | ![-](media/no.svg)        |
| Tool dimension sketch for built-in tools   | ![X](media/check.svg) | ![-](media/no.svg)        |
| Can be used standalone outside of FreeCAD  | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides built-in common shapes            | ![X](media/check.svg) | ![-](media/no.svg)        |
| Store tool notes and additional info       | ![X](media/check.svg) | ![-](media/no.svg)        |
| Auto-generates tool icons                  | ![X](media/check.svg) | ![-](media/no.svg)        |
| Can be used with no document open          | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides CLI tool for import/export        | ![X](media/check.svg) | ![-](media/no.svg)        |
| Read BTL files                             | ![X](media/check.svg) | ![X](media/check.svg)     |
| Write BTL files                            | ![X](media/check.svg) |  Deletes BTL extra data!  |
| Import from Camotics                       | ![X](media/check.svg) | ![-](media/no.svg)        |
| Export to Camotics                         | ![X](media/check.svg) | ![X](media/check.svg)     |
| Export to LinuxCNC                         | ![X](media/check.svg) | ![X](media/check.svg)     |

## Installation via the FreeCAD addon manager

- Open FreeCAD
- Go to *Edit -> Preferences -> Addon Manager*
- Click "+"
- Enter the following Repository URL: `https://github.com/knipknap/better-tool-library`
- Enter the branch name `main`
- Click confirm
- Open the Addon Manager via *Tools -> Addon manager*
- Search for *Better Tool Library*
- Click it
- Click *Install*

To run it, just **open the Path workbench** and there should be a new icon at the end of the
toolbar:

![Toolbar](media/toolbar.png)

## Screenshots

![Library Editor](media/library.png)
![Shape Browser](media/shape-browser.png)
![Tool Editor](media/tool-editor.png)

## Standalone mode

To use via standalone, you will have to install BTL via setuptools.

```
pip install btl
```

Alternative installation for the development version:

```
git clone https://github.com/knipknap/better-tool-library.git
```

To run this, you need to point `qbtl` to your FreeCAD directories:

```
export PYTHONPATH=/usr/share/freecad/Ext/:/usr/lib/freecad/lib/
qbtl path/to/your/toollibrary/
```

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
