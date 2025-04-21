'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


import time

from spasic.util.syswatchdog import SystemWatchdog
from spasic.experiment_runner.experiment import Experiment

#### Sample "experiments" ####

def exp_return_byte():
    print("returning a byte")
    time.sleep(3)
    return 0x42
    
def exp_return_longint():
    print("returning sys time")
    time.sleep(4)
    return time.time()
    
def exp_return_str():
    print("Returning a string")
    time.sleep(3)
    return "hello there!"
    
def exp_return_array():
    print("returning array")
    time.sleep(5)
    return [1,2,3,4,5,6,7,8,9,10]
    
def exp_return_bytes():
    print("returning array")
    time.sleep(5)
    b = bytearray(16)
    for i in range(16):
        b[i] = i+42
    
    return b
    
def exp_throws():
    print("throwing exception")
    time.sleep(4)
    a = int('hohohononono')
    return a

def exp_deadbeat():
    print("Running func that hangs forever...")
    while True:  # Hangs forever
        pass
    return "Done"


## system test running each experiment ##
def system_test():
    exp_funcs = [
        exp_return_byte,
        exp_return_longint,
        exp_return_str,
        exp_return_array,
        exp_return_bytes,
        exp_throws,
        exp_deadbeat
    ]
    
    singleExpTimeoutSecs = 11
    
    experiments = list(map(lambda i: Experiment(i, singleExpTimeoutSecs, exp_funcs[i]), range(len(exp_funcs))))
    wd = SystemWatchdog()
    for ex in experiments:
        print(f'\n\nTriggering {ex}')
        eResult = wd.run(ex)
        print()
        print(eResult)
        print(f'Report: {eResult.report}')
        

if __name__ == '__main__':
    system_test()
    