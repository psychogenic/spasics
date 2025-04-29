'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
DefaultGCThreshold = 50000
# import _thread
import gc
gc.threshold(10000)
import micropython 

import time 

from spasic.util.coresync import CoreSynchronizer
import i2c_server 
from i2c_server import *
# import test_space
import spasic.settings as sts

gc.threshold(DefaultGCThreshold)


# _thread.stack_size(0)  # Set stack size to 8KB

def mainTestInThread():
    coreSync = CoreSynchronizer()
    if sts.StartupDelaySeconds:
        print(f'Waiting {sts.StartupDelaySeconds}s to start...')
        time.sleep(sts.StartupDelaySeconds)
        
    print("Start-up!  Launching testspace handler...")
    test_space.handler_launch(coreSync)
    print("Entering i2c mainloop")
    i2c_server.main_loop(coreSync)
    
    
def mainServerInThread():
    coreSync = CoreSynchronizer()
    if sts.StartupDelaySeconds:
        print(f'Waiting {sts.StartupDelaySeconds}s to start...')
        time.sleep(sts.StartupDelaySeconds)
        
    print("Start-up!  Launching server thread...")
    i2c_server.server_launch(coreSync)
    print("Entering testspace mainloop")
    
    test_space.requestHandler(coreSync)
    

def ttit():
    gc.threshold(8000)
    micropython.mem_info()
    from ttboard.demoboard import DemoBoard
    print("getting")
    gc.collect()
    micropython.mem_info()
    tt =  DemoBoard.get()
    gc.threshold(DefaultGCThreshold)
    return tt

if __name__ == '__main__':
    if sts.StartupDelaySeconds:
        print(f'Waiting {sts.StartupDelaySeconds}s to start...')
        time.sleep(sts.StartupDelaySeconds)
    
    micropython.mem_info()
    print("Start-up!  Launching server...")
    Debug = False 
    if Debug:
        coreSync = CoreSynchronizer()
        i2c_dev = get_i2c_device()
        in_data_parser = get_data_parser(coreSync)
    else:
        i2c_server.main_loop()