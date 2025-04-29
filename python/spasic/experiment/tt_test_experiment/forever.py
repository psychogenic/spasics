'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def run_experiment(params:ExperimentParameters, response:ExpResult):
    print("This experiment will run until you tell it to stop")
    try:
        count = 0
        response.result = bytearray(4)
        while params.keep_running:
            count += 1
            if count > 0xffffff:
                count = 0
                
            response.result = count.to_bytes(4, 'little')
            time.sleep(0.25)
    except Exception as e:
        response.exception = e 
    else:
        response.completed = True
    return