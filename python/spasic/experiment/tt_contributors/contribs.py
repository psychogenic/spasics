'''
Created on May 7, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def contributors(params:ExperimentParameters, response:ExpResult):
    
    people = [
            b'Pat Deegan',
            b'Matt Venn',
            b'Uri Shaked',
            b'Sylvain Munaut',
            b'Tamas H.',
            b'Stuart Childs',
            b'Claire Elliot',
            b'Florian S.'
        ]
    
    for p in people:
        response.result = bytearray(p)
        for _i in range(10):
            time.sleep_ms(100)
            if not params.keep_running:
                return 
            
    lottery_winner = random.choice(people)
    
    response.result = bytearray(lottery_winner)
    
    return
            