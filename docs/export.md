# BTL import/export formats

## LinuxCNC

BTL can **export** tools in the LinuxCNC .tbl format:

```
T1 P1 D1.0 ;2,5mm uncoated aluminium dual flute HRC50
T6 P6 D12.65 ;D12,65mm L26mm S8 2 flute wood router bit
T14 P14 D2.5 ;2,5mm dual flute ball nose
T23 P23 D1.5 ;HM TiAln coated endmill 1,5mm 4 flute
T24 P24 D3.17 ;3,175mm single flute DLC coated Hozly
T38 P38 D1.0 ;2,5mm uncoated aluminium dual flute HRC50
```

### CLI support

You can also use the CLI tool to make these files.
The following command exports all libraries into a folder:

```
btl my-tool-dir/ export -f linuxcnc linuxcnc-export/
```

This folder will contain one .tbl file per library.


## Camotics

Camotics files can be **exported** and also **imported**.

To import, go to **File -> Import library...**, choose Camotics in the file
filter, and click **Open**. All tools from the selected Camotics file will
be imported into the currently selected library.

### CLI support

The following command exports all libraries into a folder
in Camotics format:

```
btl my-tool-dir/ export -f camotics camotics-export/
```

The output folder will contain one .ctbl file per library.
Example output:

```
{
  "1": {
    "units": "metric",
    "shape": "Cylindrical",
    "length": 40.0,
    "diameter": 1.0,
    "description": "2,5mm uncoated aluminium dual flute HRC50"
  }
}
```
