'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


from spasic.cnc.handler.base import HandlerBase
from spasic.cnc.command.schedule import ScheduleCommand, Command
import spasic.cnc.command.schedule as schcmd
import spasic.error_codes as err_codes
import spasic.cnc.response.response as rsp
import spasic.experiment.experiment_map as exp_map
from spasic.experiment_runner.experiment import Experiment
import spasic.settings as sts

class ScheduleCmdHandler(HandlerBase):
    def __init__(self, coreSync, wdogAndRunner):
        super().__init__(coreSync, wdogAndRunner)
        
    def can_handle(self, cmd:Command):
        return isinstance(cmd, ScheduleCommand)
    
    
    def handle(self, cmd:ScheduleCommand):
        hndlmap = {
            schcmd.RunImmediate: self.handle_runimmediate,
            }
        
        if type(cmd) in hndlmap:
            f = hndlmap[type(cmd)]
            return f(cmd)
        
        return False
        
    def handle_runimmediate(self, cmd:schcmd.RunImmediate):
        print(f'Running {cmd.experiment_id}')
        
        selected_experiment = None
        for exp in exp_map.Experiments:
            if exp.id == cmd.experiment_id:
                selected_experiment = exp 
                break 

        if selected_experiment is None:
            self.respond_error(err_codes.UnknownExperiment, cmd.experiment_id.to_bytes(2, 'little'))
            return 
        
        exp = Experiment(selected_experiment.id, sts.MaxExperimentDurationDefaultSeconds, 
                         selected_experiment.run)

        self.run(exp) # will be queued
        
        print(f'Queued')
        respmsg = b'EXP'
        respmsg += selected_experiment.id.to_bytes(2, 'little')
        self.respond(rsp.ResponseOKMessage(respmsg))
        # self.respond(rsp.ResponseExperiment(selected_experiment.id, experimentVal.report))
        return True 
    