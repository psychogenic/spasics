'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.experiment_runner.experiment import ExperimentResponse

class AvailableExperiment:
    def __init__(self, exp_id:int, name:str, run_func):
        self.id = int(exp_id)
        self.name = name 
        self.run = run_func
    
    def __repr__(self):
        return f'<Experiment [{self.id}] {self.name}>'

