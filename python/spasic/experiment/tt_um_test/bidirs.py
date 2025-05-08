'''
Created on May 7, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def test_bidirectionals(params:ExperimentParameters, response:ExpResult, num_iterations:int=50):
    # we'll send a simple response result, 7 bytes
    # FAILURECOUNT[0..3]  NUM_ITERATIONS CURRENT_ITERATION INTERRUPTED
    response.result = bytearray(7)
    
    # num iterations won't change, so we can stick this in 
    # the response immediately
    response.result[4] = num_iterations
    
    # get the TT DemoBoard object from params passed in
    tt = params.tt 
    
    # Use the TT object to load your design
    tt.shuttle.tt_um_factory_test.enable()
    
    # want to clock at some rate
    tt.clock_project_PWM(1000)
    
    # setup my inputs: 0 for reflection mode
    tt.ui_in[0] = 0
    
    # set bidirs to outputs
    tt.uio_oe_pico.value = 0xff
    
    
    failure_count = 0 # this is our main report value
    for it in range(num_iterations):
        print(f"loop {it}...", end='')
        response.result[5] = it
        # reset project
        tt.reset_project(True)
        
        tt.clock_project_once() # tick
    
        # release from reset
        tt.reset_project(False)
        
        for i in range(256):
            
            # inside tightest loop, keep checking if 
            # termination has been requested
            if not params.keep_running:
                # have been asked to terminate, make note and return
                response.result[6] = 1
                return 
            
            
            tt.uio_in.value = i
            time.sleep_ms(1) # settle time
            if tt.uo_out.value != i:
                failure_count += 1
                if failure_count % 10 == 0:
                    print(f"bidir mismatch {i} != {int(tt.uo_out.value)}")
                # also, update response right away, both in case 
                # we're interrupted and so status updates while 
                # running report current count
                response.result[0:4] = failure_count.to_bytes(4, 'little')
            
    