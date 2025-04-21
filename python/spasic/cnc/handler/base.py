'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.util.syswatchdog import SystemWatchdog
from spasic.cnc.command.command import Command
from spasic.experiment_runner.experiment import Experiment

class HandlerBase:
    def __init__(self, wdogAndRunner:SystemWatchdog):
        self._wdogAndRunner = wdogAndRunner
        
    def reboot(self):
        self._wdogAndRunner.force_reset()
        
    def run(self, exp:Experiment):
        return self._wdogAndRunner.run(exp)
    
    def can_handle(self, cmd:Command):
        return False
    
    def handle(self, cmd:Command):
        return False