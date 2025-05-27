# SPELL

Project documentation: https://tinytapeout.com/runs/tt06/tt_um_urish_spell

This experiment runs a simple SPELL and sends the output down the satellite link.

## Expected results

The experiment should progress as follows:

| Stage                     | Reported bytes                                    |
|---------------------------|---------------------------------------------------|
| Write the SPELL to memory | `0x1 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0`         |
| Execute the SPELL         | `0x2 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0`         |
| Final result              | `0x73 0x70 0x41 0x53 0x49 0x43 0x73 0x24 0x0 0x0` |

The final result is the ASCII representation of the string "spASICs$".

