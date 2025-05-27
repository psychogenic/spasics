# LISA

This experiment runs a simple LISA test and sends the output down the satellite link.
The processor is fed opcodes via a PIO programmed from Python with up to 64 16-bit
opcodes PUSHed to the PIO FIFOs.  Then the processor is either single-stepped
or breakpoints are set and the core is allowed to run to the breakpoint.  Then additional
opcodes are PUSHed to the FIFO, additional breakpoints, etc.

After performing a series of basic LISA opcode tests, the code goes into a short loop
sending the string "LISA" via the UART2 peripheral.  This routes to RP2040 UART1, so
the Python code accumulates the received bytes and tests for receipt of the string.  Also
in that test loop, the LISA timer1 peripheral is enabled to generate 127ms "ticks".  The
running code waits for the timer rollover and increments a counter each time,  The total
timer1 "ticks" and receipt of "LISA" strings is recorded in two of the receive bytes.

If for any reason the processor fails to HALT at a prescribed breakpoint (i.e. some failure
occurred), then Python will record the expected address:

 - Expected PC:  response.result[1] (upper two PC bits in result[0][7:6])
 - Actual PC:    response.result[2] (upper two PC bits in result[0][5:4]).

If no error in PC breakpoints, at the end of the test, LISA will set the last result[9] byte
to 1 and copy LISA's calculation of the answer to "Life, The Universe and Everything" in
BF16 Floating point format to result[1] and result[2].  This value is calculated as one of the
opcode tests for FMUL as "sqrt(42) * sqrt(42)" and stored in the DFFRAM.  As it turns out,
the BF16 encoding for 42.0 also contains HEX 0x42, so it is reporting the "Answer" in two
formats.  :)

## Expected results

The experiment should progress as follows:

| Stage                      | Reported bytes                                     |
|----------------------------|----------------------------------------------------|
| LISA Debugger detected     | `0x1  0x0  0x0  0x0  0x0  0x0  0x0  0x0  0x0  0x0` |
| LISA Configuration Success | `0x2  0x0  0x0  0x0  0x0  0x0  0x0  0x0  0x0  0x0` |
| LISA Single Step Success   | `0xf  0x0  0x0  0x0  0x0  0x0  0x0  0x0  0x0  0x0` |
| LISA Opcode Tests Pass     | `0xf  0x0  0x0  0xff 0xff 0xff 0x7f 0x0  0x0  0x0` |
| Final result               | `0xf  0x42 0x28 0xff 0xff 0xff 0x7f 0x24 0x7  0x1` |
                                     ---------                       ^    ^    ^ 
                                   BF16 42.0 (Calculated)            |    |    |
                             "Life, the Universe and Everything"     |    |  Success
                                         ^                           |    |
                                         |                           | Number of "LISA"
                               Also reports expected                 | strings received from
                               and actual PC if break                | LISA UART2 by RP2040
                               failed.  Then  "Success"              |
                               byte will be 0x00             Number of times the 
                                                             127ms timer rolled over


