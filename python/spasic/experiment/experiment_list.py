'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import spasic.experiment.tt_um_test.loader
import spasic.experiment.tt_test_experiment.failer
import spasic.experiment.tt_test_experiment.forever
import spasic.experiment.tt_um_factory_test.loader
import spasic.experiment.tt_um_fstolzcode.loader
import spasic.experiment.tt_contributors.loader
import spasic.experiment.tt_um_oscillating_bones.loader

ExperimentsAvailable = {
    
        # 1 sample experiment
        1: spasic.experiment.tt_um_test.loader.run_experiment,
        
        2: spasic.experiment.tt_um_fstolzcode.loader.run_experiment,
        
        3: spasic.experiment.tt_um_oscillating_bones.loader.run_experiment,
        
        
        0x80: spasic.experiment.tt_contributors.loader.thank_contribs,
        
        # 1 testing a failure
        0x81: spasic.experiment.tt_test_experiment.failer.run_experiment,
        
        # 2 factory test experiment 1
        0x82: spasic.experiment.tt_um_factory_test.loader.run_experiment,
        
        # 3 runs forever
        0x83: spasic.experiment.tt_test_experiment.forever.run_experiment
    
    }

