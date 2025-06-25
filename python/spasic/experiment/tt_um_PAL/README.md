# Easy PAL

This experiment programs the Easy PAL by Matthias Musch using all 11 product terms,
all 8 inputs and all 5 outputs.  The PAL is used as a Finite State Machine "next state"
logic block to detect passing of simple ASCII 5-bit encoded (ALL CAPS) strings.  If 
the next character is detectd, the PAL generates a 3-bit "Next state" along with a "valid"
signal.  Then the Python code implementes the 3-bit "FLOP FLOP" state variable based on
receiving a "valid" signal.  When the full string has been received, the PAL generates
a "done" signal.

The test case can currently detect one of two strings:

 params.argument_bytes[0] == 0:  "HELLO SPACE"
 params.argument_bytes[0] == 1:  "DON'T PANIC"

The test programs the PAL bitstream then passes the string to it's inputs one character
at a time, monitoring the 'valid' and 'next_state' outputs after each.o

If the test is successful, it returns either:

  "Why Hello\0"  or
  "42\0"

If the test faile it will report:

  "FAIL\0" with two bytes indicating the state, and the character it was expecting.


Equations used for the PAL:
===============================

"HELLO WORLD":

T0  = ~I7 & ~I6 & ~I5 & ~I4 &  I3 & ~I2 & ~I1 & ~I0     # S=0  H
T2  = ~I7 & ~I6 &  I5 & ~I4 & ~I3 &  I2 & ~I1 &  I0     # S=1  E
T4  = ~I7 &  I6 & ~I5 & ~I4 &  I3 &  I2 & ~I1 & ~I0     # S=2  L
T6  = ~I7 &  I6 &  I5 & ~I4 &  I3 &  I2 & ~I1 & ~I0     # S=3  L
T7  =  I7 & ~I6 & ~I5 & ~I4 &  I3 &  I2 &  I1 &  I0     # S=4  O
T8  =  I7 & ~I6 &  I5 & ~I4 & ~I3 & ~I2 & ~I1 & ~I0     # S=5  SPACE
T9  =  I7 &  I6 & ~I5 &  I4 & ~I3 & ~I2 &  I1 &  I0     # S=6  S
T10 =  I7 &  I6 &  I5 &  I4 & ~I3 & ~I2 & ~I1 & ~I0     # S=7  P
T1  = ~I7 & ~I6 & ~I5 & ~I4 & ~I3 & ~I2 & ~I1 &  I0     # S=0  A
T3  = ~I7 & ~I6 &  I5 & ~I4 & ~I3 & ~I2 &  I1 &  I0     # S=1  C
T5  = ~I7 &  I6 & ~I5 & ~I4 & ~I3 &  I2 & ~I1 &  I0     # S=2  E

O0 = T0 | T1 | T4 | T5 | T7 | T9                               # S[0]
O1 = T2 | T3 | T4 | T5 | T8 | T9                               # S[1]
O2 = T6 | T7 | T8 | T9                                         # S[2]
O3 = T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10     # VALID
O4 = T5                                                        # DONE

Equations = [O0, O1, O2, O3, O4]


"DON'T PANIC":

T0  = ~I7 & ~I6 & ~I5 & ~I4 & ~I3 &  I2 & ~I1 & ~I0     # S=0  D
T2  = ~I7 & ~I6 &  I5 & ~I4 &  I3 &  I2 &  I1 &  I0     # S=1  O
T4  = ~I7 &  I6 & ~I5 & ~I4 &  I3 &  I2 &  I1 & ~I0     # S=2  N
T6  = ~I7 &  I6 &  I5 &  I4 &  I3 &  I2 &  I1 &  I0     # S=3  ' (0x1F)
T7  =  I7 & ~I6 & ~I5 &  I4 & ~I3 &  I2 & ~I1 & ~I0     # S=4  T
T8  =  I7 & ~I6 &  I5 & ~I4 & ~I3 & ~I2 & ~I1 & ~I0     # S=5  SPACE
T9  =  I7 &  I6 & ~I5 &  I4 & ~I3 & ~I2 & ~I1 & ~I0     # S=6  P
T10 =  I7 &  I6 &  I5 & ~I4 & ~I3 & ~I2 & ~I1 &  I0     # S=7  A
T1  = ~I7 & ~I6 & ~I5 & ~I4 &  I3 &  I2 &  I1 & ~I0     # S=0  N
T3  = ~I7 & ~I6 &  I5 & ~I4 &  I3 & ~I2 & ~I1 &  I0     # S=1  I
T5  = ~I7 &  I6 & ~I5 & ~I4 & ~I3 & ~I2 &  I1 &  I0     # S=2  C

O0 = T0 | T1 | T4 | T5 | T7 | T9                               # S[0]
O1 = T2 | T3 | T4 | T5 | T8 | T9                               # S[1]
O2 = T6 | T7 | T8 | T9                                         # S[2]
O3 = T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10     # VALID
O4 = T5                                                        # DONE

