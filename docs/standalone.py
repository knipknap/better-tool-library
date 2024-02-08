# Running BTL in Standalone Mode

BTL can be started without opening FreeCAD, but you still need to have
FreeCAD installed.

To run the UI in standalone mode, you also need to tell BTL where your
FreeCAD directories are by pointing `qbtl` to it.

In Linux, this looks like that:

```
export PYTHONPATH=/usr/share/freecad/Ext/:/usr/lib/freecad/lib/
qbtl path/to/your/toollibrary/
```

Of course you will have to adapt the path according to your system
environment.

Note that in standalone mode there are some minor limitations, e.g.
BTL cannot generate any new tool icons. But everything else should
work fine.
