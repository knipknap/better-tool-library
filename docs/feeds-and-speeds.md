# Better Tool Library - Feeds & Speeds calculator

The built-in Feeds & Speeds Calculator may be one of the most powerful on the
market. It isn't just a "naive, basic, calculator", but rather an optimizing
calculator that "renders and simulates" your tool.

It can also visualize the result.

Credits: The algorithm is based on the work done by Bryan Turner.
Check out [his work](https://github.com/brturn/feeds-and-speeds)!


## Features

It takes into account a dozen of factors:

| Factor                                     |
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


## Known Limitations

- Only the following types of tools are supported:
  - Square endmills
  - Torus (=rounded corners)
  - Ballend
  - Chamfer
  - V-Bit

- Tools that are wider than they are long (stickout) are not supported.

- SI units (metric) only. While the backend already has support for converting to/from
  imperial, this is not used in the UI. If you want this feature, please submit a pull
  request.


## Screenshots

![Feeds & Speeds](../media/feeds-and-speeds.png)


## Instructions

- First, make sure your tool is all set up and all parameters are correct. The tool
  material is especially important (HSS, Carbide).

- If your tool does NOT have a chipload defined (i.e. chipload = 0), then the calculator
  will estimate an ideal chipload for you, based on the material of the tool,
  and the material you are milling.

- Then, switch to the Feeds / Speeds tab. For the initial setup, you will have to
  define a machine by pressing the "+"  button. This is a one-time activity, BTL
  will remember your machine.

- Note about machine parameters: The torque is important and has a big impact on
  the calculator. If in doubt, aim low. For reference, my 2.2 kW China spindle
  provides realistic results at around 4 Nm max torque.

- The stickout is also very, very important. By default, BTL estimates the stickout
  to be the Flute Length + 3mm. Try to minimize stickout for a better result.

- If you want to contribute more materials, check out the required parameters
  [here](../btl/feeds/material.py).
