'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

# optional argument bytes:
#  0: num iterations
#  1: experiment 1 (0), experiment 2 (non zero)
def run_experiment(params:ExperimentParameters, response:ExpResult):
    print("Made it to loader, importing")
    try:
        # optional number of iterations through test loop to do
        num_iter = params.argument_bytes[0]
        if num_iter == 0:
            num_iter = 50 # default
            
        # which experiment should we run?
        if params.argument_bytes[1]:
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