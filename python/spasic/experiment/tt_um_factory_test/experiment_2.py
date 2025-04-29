'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import time

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters


def test_counter(params:ExperimentParameters, response:ExpResult, num_iterations:int=10):
    print("test_counter")
    
    # NUMITER ABORTED FAILURES_COUNT[0..3] FAILURES_REFLECT[0..3] 
    response.result = bytearray(10)
    tt = params.tt
    # select the project
    tt.shuttle.tt_um_factory_test.enable()
    tt.clock_project_stop() # will clock manually
    
    tt.uio_oe_pico.value = 0 # all inputs on our side
    
    tt.ui_in.value = 0b1

    
    response.result[0] = num_iterations
    
    num_failures_reflect = 0
    num_failures_count = 0
    for _it in range(num_iterations):
        # reset
        tt.rst_n.value = 0
        tt.clock_project_once()
        tt.rst_n.value = 1
        tt.clock_project_once()
        for i in range(256):
            
            if not params.keep_running:
                print("Aborted")
                response.result[1] = 1
                return 
            if tt.uo_out.value != tt.uio_out.value:
                num_failures_reflect += 1
            if int(tt.uo_out.value) != i:
                num_failures_count += 1
            
            # update response result
            response.result[2:] = num_failures_count.to_bytes(4, 'little') \
                                    + num_failures_reflect.to_bytes(4, 'little')
            
            # clock it
            tt.clock_project_once()
        