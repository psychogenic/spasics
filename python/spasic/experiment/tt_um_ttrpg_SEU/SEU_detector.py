'''
Created on Apr 30, 2025

@author: Jonas Nilsson

SEU tester
Stores a predefined bytearray in the 8 byte I2C memory of design 105
Reads back values once a second and counts errors found
Returns:
  results[0:8] = Memory contents from last seen error
  results[8]   = Number of errors found
  results[9]   = Duration of experiment in minutes plus error flags

Error flags are:
  +128 on an I2C error
  +64 on premature termination (runner.abort())
  Flags will be incorrect if runtime is> 63 minutes.

Memory content set by params[0:8] if params[8]==1, defaults to 0xAA55AA55...
Experiment duration in minutes set by timeout argument in call of test_SEU
or be overridden by params[9] when non-zero.
'''
import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters
from machine import Pin, SoftI2C

def test_SEU(params:ExperimentParameters, response:ExpResult, timeout=30):

    # Get initial memory contents and timeout value from params or use default
    if params.argument_bytes[8] == 1:
       mem_contents = params.argument_bytes[0:8]
    else:
       mem_contents = bytearray(b'\xAA\x55\xAA\x55\xAA\x55\xAA\x55')
    
    if params.argument_bytes[9] != 0:
       timeout = params.argument_bytes[9]
    
    # The response is ten bytes:
    # 0-7: Data from last erroneous memory read
    # 8: Error count
    # 9: Experiment duration in minutes plus error flags

    response.result = bytearray(10)
    # get the TT DemoBoard object from params passed in
    tt = params.tt
    tt.shuttle.tt_um_sanojn_ttrpg_dice.enable()
    tt.reset_project(True)
    tt.clock_project_once() # tick
    tt.reset_project(False)

    # Set clock for proper I2C comm
    tt.clock_project_PWM(10000000)
    tt.uio_oe_pico.value = 0 
    tt.ui_in[0] = 0
    i2c=SoftI2C(scl=Pin(23),sda=Pin(22),freq=100000)
    p=Pin(23)
    p.init(pull=Pin.PULL_UP)
    p=Pin(22)
    p.init(pull=Pin.PULL_UP)
    i2c.writeto_mem(112,0,mem_contents)
    # Stop clock to conserve energy (as if it matters...)
    tt.clock_project_stop()

    for t in range(1,timeout*60+1): # approx 1 second per iteration

      for s in range(4):  
          time.sleep_ms(247) ## 250ms, but account for delays in code outside the inner loop
          if not params.keep_running:
            # We've been asked to terminate. Indicate reason in results array
            response.result[9] += 64
            return

      response.result[9] = t//60 # Indicate running time in results array
      # This runs once a second
      # Restart clock and verify memory contents
      tt.clock_project_PWM(10000000)
      time.sleep_ms(10)
      readout = i2c.readfrom_mem(112,0,8)
      if len(readout) < 8:
          # Retry once in case the i2c slave has malfunctioned. It should recover from error
          # states whenever it sees a START or STOP, so one retry fixes many potential problems
          readout = i2c.readfrom_mem(112,0,8)
          if len(readout) < 8:
             response.result[9] += 128 # Give up and report I2C error
             return

      if readout != mem_contents:
          response.result[8] += 1          # Update error counter
          response.result[0:8] = readout   # and last error found
          i2c.writeto_mem(112,0,mem_contents) # Refresh memory contents

      tt.clock_project_stop()
      if response.result[8]==255:
          return # Found lots of errors, exit prematurely

    return
