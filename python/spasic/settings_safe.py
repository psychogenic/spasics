'''
Created on Jun 25, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
# TODO FOR RELEASE: WDOG True, POST True? RaiseAndBreak False, Delay 0
WatchdogEnable = True 
PerformPOSTTest = False
RaiseAndBreakMainOnException = False
StartupDelaySeconds = 0 # only for dev, set to 0

MinDelayForAutoReportSecs = 30
AutoReportIdleMultiplier = 4
AutoReportPeriodInfo = 15
AutoReportPeriodStatus = 10

DeviceAddress = 0x56
I2CSCL = 3
I2CSDA = 2
I2CBaudRate = 100000
I2CPullups = False
I2CUsePollingDefault = True

ThreadStackSize = 4096

DebugUseSimulatedI2CDevice = False

DisableRebootsWithoutWatchdog = True 

RebootResponseDelaySeconds = 3

