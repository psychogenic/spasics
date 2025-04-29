'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

from machine import Timer, reset, WDT

import spasic.settings as sts

SystemWatchdogTimerTimeoutMs = 6500
class SystemWatchdog:
    def __init__(self, timer_period_ms=2000):
        
        if timer_period_ms > (SystemWatchdogTimerTimeoutMs / 2):
            print("Won't allow timer period more than half the WDT timeout")
            timer_period_ms = int(SystemWatchdogTimerTimeoutMs / 2)
            
        self.timer_period_ms = timer_period_ms
        self.keepFeeding = False
        self.timer = Timer(-1)
        self.wdt = None 
        self.enabled = False
        
    def stop_feeding(self):
        self.keepFeeding = False
        
    def feed_watchdog(self, _timer=None):
        if self.wdt is not None and self.keepFeeding:
            self.wdt.feed() # yum!
        
        
    def enable(self):
        if self.enabled:
            raise Exception('Already enabled')
        
        self.enabled = True
        self.keepFeeding = True
        self.timer.init(period=self.timer_period_ms, mode=Timer.PERIODIC, callback=self.feed_watchdog)
        if sts.WatchdogEnable:
            self.wdt = WDT(timeout=SystemWatchdogTimerTimeoutMs)  
        else:
            print("WATCHDOG DISABLED IN CONFIG!")