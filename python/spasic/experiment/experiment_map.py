'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.experiment_runner.available import AvailableExperiment


import spasic.experiment.tt_um_factory_test.loader 

Experiments = [
    AvailableExperiment(0, 'fact_test', spasic.experiment.tt_um_factory_test.loader.run_experiment)
]
