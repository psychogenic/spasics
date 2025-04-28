'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.experiment_runner.experiment import ExperimentResponse

def run_experiment(response:ExperimentResponse):
    print("Made it to loader, importing")
    import spasic.experiment.tt_um_factory_test.experiment_1 as exp1
    print("Import done, calling test")
    exp1.test_loopback(response, num_iterations=5)
    return