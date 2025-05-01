'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

# optional argument bytes:
# NUM_ITERATIONS[0..1]  RUN_COUNTER
# 0:2                   2
def run_experiment(params:ExperimentParameters, response:ExpResult):
    print("Made it to loader, importing")
    try:
        # optional number of iterations through test loop to do
        num_iter = int.from_bytes(params.argument_bytes[0:2], 'little')
        if num_iter == 0:
            num_iter = 50 # default
            
        # which experiment should we run?
        if params.argument_bytes[2]:
            # counter
            import spasic.experiment.tt_um_factory_test.experiment_2 as exp2
            exp2.test_counter(params, response, num_iterations=num_iter)
        else:
            # loopback
            import spasic.experiment.tt_um_factory_test.experiment_1 as exp1
            exp1.test_loopback(params, response, num_iterations=num_iter)
            
    except Exception as e:
        response.exception = e 
        print(e)
    else:
        response.completed = True
    return