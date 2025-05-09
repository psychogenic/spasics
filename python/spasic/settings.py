'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
# TODO FOR RELEASE: WDOG True, POST True? RaiseAndBreak False, Delay 0
WatchdogEnable = True 
PerformPOSTTest = True
RaiseAndBreakMainOnException = False
StartupDelaySeconds = 0 # only for dev, set to 0


DeviceAddress = 0x56
I2CSCL = 3
I2CSDA = 2
I2CBaudRate = 100000
I2CPullups = True
I2CUsePollingDefault = True

#ThreadStackSize = 8192
ThreadStackSize = 0 # 8448 # 7168 # 10240 # 9216 # 8192 # 6144 # 18432


DebugUseSimulatedI2CDevice = False

DisableRebootsWithoutWatchdog = True 

RebootResponseDelaySeconds = 3 # TODO: can we lower this, do we need to raise it?  Tibor!

