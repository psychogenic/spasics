'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''




DeviceAddress = 0x51
I2CSCL = 3
I2CSDA = 2
I2CBaudRate = 100000

#ThreadStackSize = 8192
ThreadStackSize = 16000

WatchdogEnable = True 


StartupDelaySeconds = 2  # only for dev, set to 0

RebootResponseDelaySeconds = 3 # TODO: can we lower this, do we need to raise it?  Tibor!

MaxExperimentDurationDefaultSeconds = 90*60