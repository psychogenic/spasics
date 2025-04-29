'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
DefaultGCThreshold = 50000

import gc
gc.threshold(10000)
import micropython 
import _thread
import time 
import i2c_server 
import spasic.settings as sts
from spasic.util.watchdog import SystemWatchdog

gc.threshold(DefaultGCThreshold)


if sts.ThreadStackSize:
    _thread.stack_size(sts.ThreadStackSize)


BigDog = None 
def enable_watchdog():
    global BigDog 
    BigDog = SystemWatchdog()
    BigDog.enable()

if __name__ == '__main__':
    
    enable_watchdog()
    
    if sts.StartupDelaySeconds:
        micropython.mem_info()
        print(f'Waiting {sts.StartupDelaySeconds}s to start...')
        time.sleep(sts.StartupDelaySeconds)
    
    print("Start-up!  Launching server...")
    Debug = False 
    if not Debug:
        # run the mainloop forever
        i2c_server.main_loop()
    else:
        from spasic.util.coresync import CoreSynchronizer
        from i2c_server import *
        coreSync = CoreSynchronizer()
        i2c_dev = get_i2c_device()
        in_data_parser = get_data_parser(coreSync)
        