'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def run_experiment(params:ExperimentParameters, response:ExpResult):
    print("This experiment will raise an exception")
    try:
        response.result = bytearray(5)
        response.result[1] = 0x99
        for i in range(100):
            response.result[0] = i 
            time.sleep(0.05)
            
        a = int('hellothere')
        response.result[1] = 0x42
    except Exception as e:
        response.exception = e 
    else:
        response.completed = True
    return