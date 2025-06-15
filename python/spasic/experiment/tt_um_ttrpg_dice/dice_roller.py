'''
Created on Apr 30, 2025

@author: Jonas Nilsson

Dice Roller
Roll several dice of various sizes. Pack the result in 10 bytes and return them.
Uses key presses with "deterministc" timing by default. If params[0] != 0, the
keypress timing is randomized by the RP.

Dice rolled are:
3xd4, 3xd6, 3xd8, 3xd10, 2xd12, 3xd20, 3xd100

Results are packed in bit groups according to the die
size and packed together to form the 80 bit result.

'''
import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters
from spasic.experiment.tt_um_ttrpg_dice.roll import roll

#Buttons
d4   =  1
d6   =  2
d8   =  4
d10  =  8
d12  = 16
d20  = 32
d100 = 64


def test_dice(params:ExperimentParameters, response:ExpResult):

    result = bytearray(10)
    # Check arguments in case we want the RP to help wih randomization
    randomize = params.argument_bytes[0]
    # get the TT DemoBoard object from params passed in
    tt = params.tt
    tt.shuttle.tt_um_sanojn_ttrpg_dice.enable()
    tt.reset_project(True)
    tt.clock_project_once() # tick
    tt.reset_project(False)
    # Clock can run fast since we don't need debouncing
    tt.clock_project_PWM(1000000)
    tt.uio_in.value      = 0b01100000
    tt.uio_oe_pico.value = 0b11100000
    tt.ui_in = 0

    result[0]  = roll(tt,d4,randomize) - 1  # Subtract to make the result 0-3 instead of 1-4   
    result[0] |= roll(tt,d6,randomize) - 1  << 2
    result[0] |= roll(tt,d8,randomize) - 1  << 5
    if not params.keep_running:
      response.result = bytearray(result[0:1])
      return
    result[1]  = roll(tt,d4,randomize) - 1     
    result[1] |= roll(tt,d6,randomize) - 1 << 2
    result[1] |= roll(tt,d8,randomize) - 1 << 5
    if not params.keep_running:
      response.result = bytearray(result[0:2])
      return
                                       
                                       
    result[2]  = roll(tt,d4,randomize) - 1     
    result[2] |= roll(tt,d6,randomize) - 1 << 2
    result[2] |= roll(tt,d8,randomize) - 1 << 5
    if not params.keep_running:
      response.result = bytearray(result[0:3])
      return
                                       
                                       
    result[3]  = roll(tt,d10,randomize) - 1      
    result[3]  = roll(tt,d10,randomize) - 1 << 4
    if not params.keep_running:
      response.result = bytearray(result[0:4])
      return
                                       

    result[4]  = roll(tt,d10,randomize) - 1
    d20Roll    = roll(tt,d20,randomize) - 1
    result[4] |= (d20Roll % 16) << 4

    result[5]  = roll(tt,d100,randomize) # Don't subtract. This die returns 00 - 99 already
    result[5] |= (d20Roll // 16) << 7
    if not params.keep_running:
      response.result = bytearray(result[0:6])
      return

                                       
    result[6]  = roll(tt,d12,randomize) - 1
    d20Roll    = roll(tt,d20,randomize) - 1
    result[6] |= (d20Roll % 16) << 4

    result[7]  = roll(tt,d100,randomize)
    result[7] |= (d20Roll // 16) << 7
    if not params.keep_running:
      response.result = bytearray(result[0:8])
      return
                                       
    result[8]  = roll(tt,d12,randomize) - 1
    d20Roll    = roll(tt,d20,randomize) - 1
    result[8] |= (d20Roll % 16) << 4

    result[9]  = roll(tt,d100,randomize)
    result[9] |= (d20Roll // 16) << 7
    response.result = bytearray(result)
    
    return
