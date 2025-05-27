'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import spasic.experiment.tt_contributors.loader
import spasic.experiment.tt_test_experiment.failer
import spasic.experiment.tt_test_experiment.forever
import spasic.experiment.tt_um_andrewtron3000.loader
import spasic.experiment.tt_um_cejmu.loader
import spasic.experiment.tt_um_factory_test.loader
import spasic.experiment.tt_um_fstolzcode.loader
import spasic.experiment.tt_um_lisa.loader
import spasic.experiment.tt_um_MichaelBell_tinyQV.loader
import spasic.experiment.tt_um_msg_in_a_bottle.loader
import spasic.experiment.tt_um_oscillating_bones.loader
import spasic.experiment.tt_um_qubitbytes_alive.loader
import spasic.experiment.tt_um_test.loader
import spasic.experiment.tt_um_ttrpg_dice.loader
import spasic.experiment.tt_um_urish_spell.loader
import spasic.experiment.wokwi_universal_gates_049.loader

ExperimentsAvailable = {
    
        # 1 sample experiment
        1: spasic.experiment.tt_um_test.loader.run_experiment,
        
        2: spasic.experiment.tt_um_fstolzcode.loader.run_experiment,

        # oscillating bones
        3: spasic.experiment.tt_um_oscillating_bones.loader.run_experiment, 
        
        # calvin!  
        4: spasic.experiment.tt_um_qubitbytes_alive.loader.run_experiment,   
        
        # SPELL
        5: spasic.experiment.tt_um_urish_spell.loader.run_experiment,
        
        # universal gates
        6: spasic.experiment.wokwi_universal_gates_049.loader.run_experiment,
        
        # Rule 30 Engine!
        7: spasic.experiment.tt_um_andrewtron3000.loader.run_experiment,
        
        # 9 TinyQV
        9: spasic.experiment.tt_um_MichaelBell_tinyQV.loader.run_experiment,
        
        # lisa  -- reboot prior, needs mem
        10: spasic.experiment.tt_um_lisa.loader.run_experiment,   
        
        # Dice roller
        11: spasic.experiment.tt_um_ttrpg_dice.loader.run_experiment,    
        
        # Pinecone
        12: spasic.experiment.tt_um_msg_in_a_bottle.loader.run_experiment,
        
        # TinyRV1 from the University of Wuerzburg
        17: spasic.experiment.tt_um_cejmu.loader.run_experiment, 
        
        
        
        ### System
        0x80: spasic.experiment.tt_contributors.loader.thank_contribs,
        
        # 1 testing a failure
        0x81: spasic.experiment.tt_test_experiment.failer.run_experiment,
        
        # 2 factory test experiment 1
        0x82: spasic.experiment.tt_um_factory_test.loader.run_experiment,
        
        # 3 runs forever
        0x83: spasic.experiment.tt_test_experiment.forever.run_experiment
    
    }

