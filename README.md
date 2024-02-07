# Better Tool Library (BTL)

Better Tool Library (BTL) is a FreeCAD addon (plugin) that replaces the built-in tool library
for the Path workbench.
It also provides a standalone tool if you want to use your library outside of FreeCAD.

> **Warning**
> I advise you make a backup of your tool library. I guarantee for nothing,
> there may be bugs.


## Feature Comparison

| Feature                                    | Better Tool Library   | FreeCAD internal library  |
| :--                                        |        :--:           |          :--:             |
| Modern UI                                  | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides a shape browser                   | ![X](media/check.svg) | ![-](media/no.svg)        |
| Tool search                                | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Powerful Feeds & Speeds calculator](docs/feeds-and-speeds.md) | ![X](media/check.svg) | ![-](media/no.svg)        |
| Tool dimension sketch for built-in tools   | ![X](media/check.svg) | ![-](media/no.svg)        |
| Can be used standalone outside of FreeCAD  | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides built-in common shapes            | ![X](media/check.svg) | ![-](media/no.svg)        |
| Store tool notes and additional info       | ![X](media/check.svg) | ![-](media/no.svg)        |
| Auto-generates tool icons                  | ![X](media/check.svg) | ![-](media/no.svg)        |
| Can be used with no document open          | ![X](media/check.svg) | ![-](media/no.svg)        |
| [CLI tool for import/export](cli.md)       | ![X](media/check.svg) | ![-](media/no.svg)        |
| Read BTL files                             | ![X](media/check.svg) | ![X](media/check.svg)     |
| Write BTL files                            | ![X](media/check.svg) |  Deletes BTL extra data!  |
| [Import Fusion 360 tool library](docs/formats.md) | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Import from Camotics](docs/formats.md)    | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Export to Camotics](docs/formats.md)      | ![X](media/check.svg) | ![X](media/check.svg)     |
| [Export to LinuxCNC](docs/formats.md)      | ![X](media/check.svg) | ![X](media/check.svg)     |


## Screenshots

![Library Editor](media/library.png)
![Shape Browser](media/shape-browser.png)
![Tool Editor](media/tool-editor.png)
![Feeds & Speeds](media/feeds-and-speeds.png)


## Installation

### Prerequisites

Better Tool Library (BTL) is compatible with FreeCAD 0.19 and 0.21.

### Installation via the FreeCAD addon manager

- Open FreeCAD
- Open the Addon Manager via *Tools -> Addon manager*
- Search for *Better Tool Library*
- Click it
- Click *Install*

To run it, just **open the Path workbench** and there should be a new icon at the end of the
toolbar:

![Toolbar](media/toolbar.png)


### Installation in standalone mode

To use via standalone, you will have to install BTL via setuptools.

```
pip install btl
```

Alternative installation for the development version:

```
git clone https://github.com/knipknap/better-tool-library.git
```

To run the UI in standalone mode, you need to point `qbtl` to your FreeCAD directories:

```
export PYTHONPATH=/usr/share/freecad/Ext/:/usr/lib/freecad/lib/
qbtl path/to/your/toollibrary/
```


## Instructions

Some instructions can be found here:

- [Feeds & Speeds calculator](docs/feeds-and-speeds.md).
- [Import/export function](docs/formats.md).
- [CLI tool](docs/cli.md).


## Links

- [License](LICENSE)
- [FreeCAD discussions](https://forum.freecad.org/viewtopic.php?t=79854)
