'''

A system to safely run arbitrary experiment code and capture results in
a standard (and very size-constrained) format.

The point here is to encapsulate experiment code in a way that can never
permanently hang the system.  The limits of uPython on the RP2 make it 
so we can't break out of a hung function from outside, so this system:

  * uses a Timer based approach to track experiment run time and 
    abort as required
    
  * uses the WDT as a fallback to ensure no failure can permanently disable
    the system, as it will force a reboot after SystemWatchdogTimerTimeoutMs
    should anything go really wrong.
    
The main implication is that, once instantiated, the SystemWatchdog will 
forever be responsible for feeding the WDT as this can't be changed or disabled
once started.

SystemWatchdog (class that handles running Experiments, and manages timeouts/resets/WDT feeding)
    
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


import time
from machine import Timer, reset, WDT
from spasic.util.coresync import CoreSynchronizer
import spasic.cnc.response.response as rsp
import spasic.settings as sts


SystemWatchdogTimerTimeoutMs = 6500

from spasic.experiment_runner.experiment import Experiment, ExperimentResult

class SystemWatchdog:
    '''
        The SystemWatchdog is used to trigger experiment runs
        and collect results for reporting, while ensuring no 
        process can hang longer than its stated maximum duration.
        
        Because of the way uPython works, it doesn't seem possible 
        to interrupt a function from without, so the watchdog will 
        force the process to abort as required by monitoring runtime
        through a timer and, if necessary, log the failure and hard 
        reset the entire system.
        
        Create the instance, then call .enable() -- from there, the 
        watchdog will be (forever) enabled, and the experiment timeout
        checking will function.  There simply is no disable().
    
    '''
    STARTUP=0
    IDLE=1
    WATCHING=2
    DONE=3
    TIMEDOUT=4
    def __init__(self, coreSync:CoreSynchronizer, timer_period_ms=2000):
        
        if timer_period_ms > (SystemWatchdogTimerTimeoutMs / 2):
            print("Won't allow timer period more than half the WDT timeout")
            timer_period_ms = int(SystemWatchdogTimerTimeoutMs / 2)
        
        self.core_sync = coreSync
        self.start_time = 0
        self.max_time = 0
        self.status = self.STARTUP
        self.timer_period_ms = timer_period_ms
        self.timer = Timer(-1)
        self.status = self.IDLE
        self.current_experiment = None
        self._exp_run_queue = []
        self.wdt = None 

    def enable(self):
        self.timer.init(period=self.timer_period_ms, mode=Timer.PERIODIC, callback=self._timer_callback)
        if sts.WatchdogEnable:
            self.wdt = WDT(timeout=SystemWatchdogTimerTimeoutMs)  
        
    def queue_experiment_run(self, exp:Experiment):
        self._exp_run_queue.append(exp)
        return True
    
    @property
    def experiment_queue_length(self):
        return len(self._exp_run_queue)
    
    def run_next_experiment(self):
        if not self.experiment_queue_length:
            return
        exp = self._exp_run_queue[0]
        if self.experiment_queue_length < 2:
            self._exp_run_queue = []
        else:
            self._exp_run_queue = self._exp_run_queue[1:]
            
        self.run(exp)
        
    def run(self, exp:Experiment):
        print(f'Running experiment {exp.id} (max duration {exp.timeout_s} secs)')
        self.current_experiment = exp
        self.start_time = time.time()
        self.max_time = self.start_time + exp.timeout_s
        experimentResult = ExperimentResult(exp, self.start_time)
        
        self.status = self.WATCHING
        try:
            # exp.run(experimentResult)
            print(f'\nRES:\t{experimentResult.result}')
            print(f'Report:\t{experimentResult.report}')
            experimentResult.run_completed = True
        except Exception as e:
            print(f'Exception while running: {e}')
            experimentResult.exception = e
            
        experimentResult.end_time = time.time()
        self.status = self.DONE
        try:
            self.core_sync.response_queue.put(rsp.ResponseExperiment(exp.id, experimentResult.report))
        except Exception as e:
            print(f'Exception creating response: {e}')
        return experimentResult
        
        
        
    def _timer_callback(self, timer):
        
        if self.wdt is not None:
            self.wdt.feed() # always, ALWAYS, feed the watchdog
        
        if self.status != self.WATCHING:
            return 
        if time.time() > self.max_time:
            print(f'TIMEOUT for {self.current_experiment}')
            self.status = self.TIMEDOUT
            self.handle_timeout()
            return 
            
        print('.', end='')
    
    def handle_timeout(self):
        # TODO: LOG RESULT, move state to next experiment, possibly disable current exp?
        print("EXPERIMENT HUNG--forcing system reset")
        self.force_reset()
        
    def force_reset(self):
        self.timer.deinit() # if reset somehow didn't work, WDT would do the job and finish us off
        self.timer = None
        time.sleep(3)
        reset()



    