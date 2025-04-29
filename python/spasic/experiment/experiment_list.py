'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import spasic.experiment.tt_test_experiment.loader
import spasic.experiment.tt_um_factory_test.loader

ExperimentsAvailable = {
    
        # 1 testing a failure
        1: spasic.experiment.tt_test_experiment.loader.run_experiment,
        
        # 2 factory test experiment 1
        2: spasic.experiment.tt_um_factory_test.loader.run_experiment
    
    }

