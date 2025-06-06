> [!WARNING]
> 2025-06-06: BTL IS DEPRECATED AND NO LONGER SUPPORTED AFTER FREECAD 1.01! The core features have been added directly into FreeCAD, so I recommend you remove the addon. While not all features are available in FC yet, I will add improvements directly into FreeCAD from now on.


# Better Tool Library (BTL)

Better Tool Library (BTL) is a [FreeCAD](https://www.freecad.org/) addon (plugin) that replaces the built-in tool library
for the CAM (previously known as the 'Path') workbench.
It also provides a standalone tool if you want to use your library outside of FreeCAD.

> [!WARNING]
> I advise you make a backup of your tool library. I guarantee for nothing, there may be bugs.

## Feature Comparison

| Feature                                            | Better Tool Library   | FreeCAD internal library  |
| :--                                                |        :--:           |          :--:             |
| Modern UI                                          | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides a shape browser                           | ![X](media/check.svg) | ![-](media/no.svg)        |
| Tool search                                        | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Powerful Feeds & Speeds calculator](docs/feeds-and-speeds.md) | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Tool sketch for supported shapes](docs/shape.md)  | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Use outside of FreeCAD](docs/standalone.md)       | ![X](media/check.svg) | ![-](media/no.svg)        |
| Provides built-in common shapes                    | ![X](media/check.svg) | ![-](media/no.svg)        |
| Store tool notes and additional info               | ![X](media/check.svg) | ![-](media/no.svg)        |
| Auto-generates tool icons                          | ![X](media/check.svg) | ![-](media/no.svg)        |
| Can be used with no document open                  | ![X](media/check.svg) | ![-](media/no.svg)        |
| [CLI tool for import/export](docs/cli.md)          | ![X](media/check.svg) | ![-](media/no.svg)        |
| Read BTL files                                     | ![X](media/check.svg) | ![X](media/check.svg)     |
| Write BTL files                                    | ![X](media/check.svg) |  Deletes BTL extra data!¹  |
| [Import Fusion 360 tool library](docs/formats.md)  | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Import from Camotics](docs/formats.md)            | ![X](media/check.svg) | ![-](media/no.svg)        |
| [Export to Camotics](docs/formats.md)              | ![X](media/check.svg) | ![X](media/check.svg)     |
| [Export to LinuxCNC](docs/formats.md)              | ![X](media/check.svg) | ![X](media/check.svg)     |

¹ The original FreeCAD CAM workbench tool editor deletes any unknown attributes from the tool when editing it. So if you use BTL to save BTL-only tool information like *Supplier* or *Description*, and then uninstall BTL and edit that tool with the FreeCAD tool editor again, the information will be erased.

## Screenshots

![Library Editor](media/library.png)
![Shape Browser](media/shape-browser.png)
![Tool Editor](media/tool-editor.png)
![Feeds & Speeds](media/feeds-and-speeds.png)


## Installation

### Prerequisites

- Better Tool Library (BTL) is compatible with any FreeCAD version greater than or equal to version 0.19.
- If you installed FreeCAD from source, you may also need to install the [Python requirements](requirements.txt). If you are using the Appimage this step is not necessary, as BTL has no requirements that are not already included in the Appimage.

### Installation via the FreeCAD addon manager

- Start FreeCAD
- Open the [Addon Manager](https://wiki.freecad.org/Std_AddonMgr) via *Tools -> Addon manager*
- Search for *Better Tool Library* and click on it
- Press *Install*
- You should see a prompt to restart FreeCAD, choose to restart

To run it, start FreeCAD and simply **open the CAM workbench**.  
There should be a new icon at the end of the toolbar:

![Toolbar](media/toolbar.png)


### Installation in standalone mode

To use BTL via standalone (=outside of FreeCAD), you will have to install it using
setuptools.

```
pip install btl
```

Instructions for running BTL that way are [here](docs/standalone.md).

## Instructions

Some instructions can be found here:

- [Feeds & Speeds calculator](docs/feeds-and-speeds.md)
- [Import/export function](docs/formats.md)
- [Running BTL outside of FreeCAD](docs/standalone.md)
- [CLI tool](docs/cli.md)


## Links

- [License](LICENSE)
- [FreeCAD discussions](https://forum.freecad.org/viewtopic.php?t=79854)
