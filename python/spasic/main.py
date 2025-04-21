'''

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import _thread
import time
from spasic.util.coresync import CoreSynchronizer
from spasic.util.syswatchdog import SystemWatchdog
from spasic.cnc.handler.handler import CommandHandler
from spasic.cnc.command.system import HeartBeat, RebootNormal, RebootSafe, SetSystemClock, Abort
from spasic.cnc.command.schedule import RunImmediate
from spasic.experiment_runner.experiment import Experiment, ExperimentResponse


def requestHandler(coreSync:CoreSynchronizer):
    
    expRunnerAndWatchdog = SystemWatchdog()
    commandHandler = CommandHandler(expRunnerAndWatchdog)
    expRunnerAndWatchdog.enable()
    
    while True:
        cmd = coreSync.command_queue.get(block=True)
        print(f'Handling command {cmd}')
        commandHandler.handle(cmd)
        

def launchHandler(coreSync:CoreSynchronizer):
    _thread.start_new_thread(requestHandler, (coreSync, ))


def scheduleReboot():
    rbtCmd = RebootNormal()
    print('Gonna put reboot in queue in 2s')
    time.sleep(2)
    coreSync.command_queue.put(rbtCmd)
    print('done')
    


coreSync = CoreSynchronizer()
    
    
    
    
    
    

def exp_return_byte(resp:ExperimentResponse):
    print("returning a byte")
    
    resp.result = 0x22 # intermediate result
    
    time.sleep(3)
    
    # final result
    return 0x42
    
def exp_return_longint(resp:ExperimentResponse):
    print("returning sys time")
    time.sleep(4)
    return time.time()
    
def exp_return_str(resp:ExperimentResponse):
    print("Returning a string")
    time.sleep(3)
    return "hello there!"
    
def exp_return_array(resp:ExperimentResponse):
    print("returning array")
    time.sleep(5)
    return [1,2,3,4,5,6,7,8,9,10]
    
def exp_return_bytes(resp:ExperimentResponse):
    print("returning array")
    time.sleep(5)
    b = bytearray(16)
    for i in range(16):
        b[i] = i+42
    
    return b
    
def exp_throws(resp:ExperimentResponse):
    print("throwing exception")
    time.sleep(4)
    resp.result = 0xdeadbeef
    a = int('hohohononono')
    return a

def exp_deadbeat(resp:ExperimentResponse):
    print("Running func that hangs forever...")
    resp.result = 0
    while True:  # Hangs forever
        resp.result += 1
        pass
    return "Done"


_impmodule = None
def facttest_experiment(tmout:int=20):
    global _impmodule
    mname = 'experiment.tt_um_factory_test'
    _impmodule = __import__(f'spasic.{mname}')
    f = eval(f"_impmodule.{mname}.main")
    return Experiment(42, 20, f)

_ftestExp = None 
def scheduleFactTest():
    global _ftestExp 
    if _ftestExp is None:
        _ftestExp = facttest_experiment()
        
    coreSync.command_queue.put(RunImmediate(_ftestExp))

## system test running each experiment ##
def scheduleAll():
    exp_funcs = [
        exp_return_byte,
        exp_return_longint,
        exp_return_str,
        exp_return_array,
        exp_return_bytes,
        exp_throws,
        # exp_deadbeat
    ]
    
    singleExpTimeoutSecs = 11
    
    experiments = list(map(lambda i: Experiment(i, singleExpTimeoutSecs, exp_funcs[i], 4), range(len(exp_funcs))))
    for exp in experiments:
        print(f'Scheduling experiment')
        coreSync.command_queue.put(RunImmediate(exp))
        
    


    
    

    