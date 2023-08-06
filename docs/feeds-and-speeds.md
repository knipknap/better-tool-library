# Better Tool Library - Feeds & Speeds calculator

The built-in Feeds & Speeds Calculator may be one of the most powerful on the
market. It isn't just a "naive, basic, calculator", but rather an optimizing
calculator that "renders and simulates" your tool.

It can also visualize the result.

Credits: The algorithm is based on the work done by Bryan Turner.
Check out [his work][1]!

## Features

It takes into account a dozen of factors:

| Check                                      |
| :--                                        |
| Tool shape                                 |
| Tool elasticity                            |
| Tool inertia                               |
| Tool endpoint deflection                   |
| Tool angular deflection                    |
| Tool min and max chipload                  |
| Tool bend limit                            |
| Tool shear strength                        |
| Tool shank vs flute strength               |
| Material/Tool-specific power factor        |
| Material/Tool-specific chipload table      |
| Material/Tool-specific min/max speeds      |
| Spindle power                              |
| Spindle torque (naive torque curve)        |
| Spindle min/max RPM                        |
| Machine feed limit                         |


## Current Limitations

- Only the following types of tools are supported: Square endmills, torus (=rounded corners),
  ballend, and chamfer (v-bit).

- Tools that are wider than they are long (stickout) are not supported.

- The Feeds & Speeds UI only supports SI units (metric). While the backend already has support
  for converting to/from imperial, this is not used in the UI. If you want to extend
  the UI, please submit a pull request.


## Screenshots

![Feeds & Speeds](../media/feeds-and-speeds.png)


[1] https://github.com/brturn/feeds-and-speeds
