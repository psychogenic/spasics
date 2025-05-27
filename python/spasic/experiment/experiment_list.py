'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import gc 

DefaultFuncName = 'run_experiment'
ModuleParent = 'spasic.experiment'
ExperimentsConfig = {
    1: ('tt_um_test.loader', None),
    2: ('tt_um_fstolzcode.loader', None),
    3: ('tt_um_oscillating_bones.loader', None),
    4: ('tt_um_qubitbytes_alive.loader', None),
    5: ('tt_um_urish_spell.loader', None),
    6: ('wokwi_universal_gates_049.loader', None),
    7: ('tt_um_andrewtron3000.loader', None),
    8: ('tt_um_MichaelBell_tinyQV.loader', None),
    9: ('tt_um_lisa.loader', None),
    10: ('tt_um_ttrpg_dice.loader', None),
    11: ('tt_um_msg_in_a_bottle.loader', None),
    12: ('tt_um_cejmu.loader', None),
    
    
    
    
    0x80: ('tt_contributors.loader', 'thank_contribs'),
    0x81: ('tt_test_experiment.failer', None),
    0x82: ('tt_um_factory_test.loader', None),
    0x83: ('tt_test_experiment.forever', None)
}
ExperimentsAvailable = {}
def getExperiment(eid:int):
    
    if eid in ExperimentsAvailable:
        return ExperimentsAvailable[eid]
    
    if eid not in ExperimentsConfig:
        return None 
    
    def_thresh = gc.threshold()
    gc.threshold(4096)
    
    
    module_path = f'{ModuleParent}.{ExperimentsConfig[eid][0]}'
    try:
        # Troy's cool import code
        mod = __import__(module_path, None, None, ['']) # [''] seems to impact absolute/relative lookup
        entry_point = ExperimentsConfig[eid][1] if ExperimentsConfig[eid][1] is not None else  DefaultFuncName
        
        gc.threshold(def_thresh)
        
        loader = getattr(mod, entry_point, None)
        if callable(loader):
            ExperimentsAvailable[eid] = loader
        else:
            # something is wrong here, don't do this again
            ExperimentsAvailable[eid] = None
    except:
        ExperimentsAvailable[eid] = None
        
    return ExperimentsAvailable[eid]

