'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

ExperimentsAvailable = {
}

def getExperiment(eid:int):
    if eid in ExperimentsAvailable:
        return ExperimentsAvailable[eid]
    
    if eid == 1:
        import spasic.experiment.tt_um_test.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_test.loader.run_experiment
    elif eid == 2:
        import spasic.experiment.tt_um_fstolzcode.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_fstolzcode.loader.run_experiment
    elif eid == 3:
        import spasic.experiment.tt_um_oscillating_bones.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_oscillating_bones.loader.run_experiment
    elif eid == 4:
        import spasic.experiment.tt_um_qubitbytes_alive.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_qubitbytes_alive.loader.run_experiment
    
    elif eid == 5:
        import spasic.experiment.tt_um_urish_spell.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_urish_spell.loader.run_experiment
    elif eid == 6:
        import spasic.experiment.wokwi_universal_gates_049.loader
        ExperimentsAvailable[eid] = spasic.experiment.wokwi_universal_gates_049.loader.run_experiment
    
    elif eid == 7:
        import spasic.experiment.tt_um_andrewtron3000.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_andrewtron3000.loader.run_experiment
        
        
    elif eid == 8:
        import spasic.experiment.tt_um_MichaelBell_tinyQV.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_MichaelBell_tinyQV.loader.run_experiment
    
    elif eid == 9:
        import spasic.experiment.tt_um_lisa.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_lisa.loader.run_experiment
    elif eid == 10:
        import spasic.experiment.tt_um_ttrpg_dice.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_ttrpg_dice.loader.run_experiment
    elif eid == 11:
        import spasic.experiment.tt_um_msg_in_a_bottle.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_msg_in_a_bottle.loader.run_experiment
    elif eid == 12:
        import spasic.experiment.tt_um_cejmu.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_cejmu.loader.run_experiment
    elif eid == 0x80:
        import spasic.experiment.tt_contributors.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_contributors.loader.thank_contribs
    elif eid == 0x81:
        import spasic.experiment.tt_test_experiment.failer
        ExperimentsAvailable[eid] = spasic.experiment.tt_test_experiment.failer.run_experiment
    elif eid == 0x82:
        import spasic.experiment.tt_um_factory_test.loader
        ExperimentsAvailable[eid] = spasic.experiment.tt_um_factory_test.loader.run_experiment
    elif eid == 0x83:
        import spasic.experiment.tt_test_experiment.forever
        ExperimentsAvailable[eid] = spasic.experiment.tt_test_experiment.forever.run_experiment
    
    if eid in ExperimentsAvailable:
        return ExperimentsAvailable[eid]
    
    return None

