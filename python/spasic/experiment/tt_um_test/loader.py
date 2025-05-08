'''
Created on Apr 30, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def run_experiment(params:ExperimentParameters, response:ExpResult):
    # always wrap everything in a try block
    try:
        # optional number of iterations through test loop to do
        num_iter = int.from_bytes(params.argument_bytes[0:2], 'little')
        if num_iter == 0:
            num_iter = 50 # default
            
        check_bidirs = params.argument_bytes[2]
            
        # which experiment should we run?
        if check_bidirs:
            # import HERE, inside the function, 
            # such that loading all the experiment runners doesn't 
            # eat a ton of memory by pre-importing everything
            import spasic.experiment.tt_um_test.bidirs
            
            spasic.experiment.tt_um_test.bidirs.test_bidirectionals(params, response, num_iterations=num_iter)
            
        else:
            # import HERE, inside the function, 
            # such that loading all the experiment runners doesn't 
            # eat a ton of memory by pre-importing everything
            import spasic.experiment.tt_um_test.counter
            
            # run that experiment
            spasic.experiment.tt_um_test.counter.test_counter(params, response, num_iterations=num_iter)
        
    except Exception as e:
        # an exception occurred... 
        # let the server know about it
        response.exception = e 
    else:
        # we get here, all went well
        # mark the experiment as completed
        response.completed = True
    return