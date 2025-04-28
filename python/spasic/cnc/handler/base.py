'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.util.coresync import CoreSynchronizer
from spasic.util.syswatchdog import SystemWatchdog
from spasic.cnc.command.command import Command
from spasic.experiment_runner.experiment import Experiment
import spasic.cnc.response.response as rsp

class HandlerBase:
    def __init__(self, coreSync:CoreSynchronizer, wdogAndRunner:SystemWatchdog):
        self._core_sync = coreSync
        self._wdogAndRunner = wdogAndRunner
        
    @property 
    def core_sync(self):
        return self._core_sync
    
    def reboot(self):
        self._wdogAndRunner.force_reset()
        
    def run(self, exp:Experiment):
        # if we just try and run() that here on the 
        # experiment watchdog, we're doing it from
        # within the handler... and we hit our nose
        # against max recursion
        # instead: queue it
        return self._wdogAndRunner.queue_experiment_run(exp)
        # return self._wdogAndRunner.run(exp)
    
    def can_handle(self, cmd:Command):
        return False
    
    def handle(self, cmd:Command):
        return False
    
    def respond(self, the_response:rsp.Response):
        self.core_sync.response_queue.put(the_response)
        
    def respond_ok(self):
        self.respond(rsp.ResponseOK())
        
    def respond_error(self, err_code:int, err_bts:bytearray=None):
        self.respond(rsp.ResponseError(err_code, err_bts))