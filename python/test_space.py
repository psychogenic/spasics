'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import _thread
from spasic.util.coresync import CoreSynchronizer
from spasic.util.syswatchdog import SystemWatchdog
from spasic.cnc.handler.handler import CommandHandler
from spasic.experiment_runner.experiment import Experiment, ExperimentResponse

ContinueHandling = True 
def requestHandler(coreSync:CoreSynchronizer):
    
    global ContinueHandling
    expRunnerAndWatchdog = SystemWatchdog(coreSync)
    commandHandler = CommandHandler(coreSync, expRunnerAndWatchdog)
    expRunnerAndWatchdog.enable()
    
    while ContinueHandling:
        cmd = coreSync.command_queue.get(block=True)
        print(f'Handling command {cmd}')
        commandHandler.handle(cmd)
        
        if expRunnerAndWatchdog.experiment_queue_length:
            expRunnerAndWatchdog.run_next_experiment()
        

def handler_launch(coreSync:CoreSynchronizer):
    _thread.start_new_thread(requestHandler, (coreSync, ))

def handler_teardown():
    global ContinueHandling
    ContinueHandling = False