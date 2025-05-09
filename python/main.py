'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import gc
DefaultGCThreshold = gc.threshold()
gc.threshold(4096)
import micropython 
import _thread
import time 
import i2c_server 
import spasic.settings as sts
import spasic.ver as ver
from spasic.util.watchdog import enable_watchdog
from ttboard.demoboard import DemoBoard

Debug = False
tt = DemoBoard.get()
gc.threshold(DefaultGCThreshold)

### 
### System-wide settings and setup
# thread stack size
if sts.ThreadStackSize:
    print(f"Setting thread stack to {sts.ThreadStackSize}")
    _thread.stack_size(sts.ThreadStackSize)

# watchdog
if sts.WatchdogEnable:
    enable_watchdog()
else:
    print("\n\nWARNING: NO WATCHDOG -- disabled in settings")

# startup delay (useful for debugz, disable otherwise)
if sts.StartupDelaySeconds:
    micropython.mem_info()
    if sts.StartupDelaySeconds:
        print(f'Waiting {sts.StartupDelaySeconds}s to start...')
        time.sleep(sts.StartupDelaySeconds)

print(f"Start-up v{ver.major}.{ver.minor}.{ver.patch}! Launching server... (debug: {Debug})")
if not Debug:
    # realdeal, startup i2c services
    i2c_server.begin()
    
    if sts.PerformPOSTTest:
        print("Performing POST")
        i2c_server.POST()
     
    i2c_server.main_loop()  
else:
    print("DEBUG mode -- TESTING ASIC/wiring")
    # test experiment uses
    # params[0:2] as num iterations (little endian)
    # and params[2] for exp selection
    if not sts.DebugUseSimulatedI2CDevice:
        # just do POST
        i2c_server.POST(5)
    else:
        # playing with simulate i2c
        print("\nXXX WARNING WARNING: using SIMULATED i2c device XXX\n")
        from i2c_simdev import *
        print("Launching mainloop as THREAD (experiment launch will return error)")
        _thread.start_new_thread(i2c_server.main_loop, (0,))
        print()
        time.sleep(0.5)
