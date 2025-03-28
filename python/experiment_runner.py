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
    
The main implication is that, once instantiated, the ExperimentWatchdog will 
forever be responsible for feeding the WDT as this can't be changed or disabled
once started.

This file includes the
    Experiment (wrapper for arbitrary functions, with an id and timeout setting)
    ExperimentResult (container for results, exceptions and meta-data)
    ExperimentWatchdog (class that handles running Experiments, and manages timeouts/resets/WDT feeding)
    
along with a system_test() that runs a variety of experiments as a demo, including one that hangs forever.
    

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com

'''

import time
from machine import Timer, reset, WDT
SystemWatchdogTimerTimeoutMs = 6500

class Experiment:
    '''
        An Experiment is something with 
         * a unique integer id
         * a function we can call;
         * a number of result bytes the function will return; and
         * a maximum execution time (in seconds).
    '''
    def __init__(self, uid:int, timeout_s:int, run_func, result_num_bytes:int=4):
        self.id = uid 
        self.result_num_bytes = result_num_bytes
        self.timeout_s = timeout_s 
        self.func = run_func 
        
    def run(self):
        f = self.func 
        return f()
        
    def __repr__(self):
        return f'<Experiment {self.id}>'
        
class ExperimentResult:
    '''
        An ExperimentResult holds the details of an experimental run.
        It knows when the experiment was started, which experiment it 
        is related to, and can return results or exceptions in a manner
        suitable for reporting.
    '''
    def __init__(self, experiment:Experiment, 
                start_time_s:int):
        self.experiment = experiment
        self.start_time = start_time_s
        self.run_completed = False
        self.end_time = 0
        self.exception = None 
        self.result = None
        
    @property
    def run_time(self):
        if self.end_time == 0:
            return 0
            
        return self.end_time - self.start_time
        
    @property
    def have_result(self):
        return self.result is not None
        
    @property 
    def have_exception(self):
        return self.exception is not None 
        
    @property 
    def exception_type_id(self):
        if not self.have_exception:
            return None 
        
        if not hasattr(self.exception, '__class__'):
            return None 
            
        ec = self.exception.__class__ 
        allExceptions = [
            ArithmeticError, # 0
            AssertionError,
            AttributeError,
            EOFError,
            Exception,
            ImportError, # 5
            IndentationError,
            IndexError,
            KeyError,
            KeyboardInterrupt,
            LookupError, # 10
            MemoryError,
            NameError,
            NotImplementedError,
            OSError,
            OverflowError, # 15
            RuntimeError,
            StopIteration,
            SyntaxError,
            SystemExit,
            TypeError,  # 20
            ValueError,
            ZeroDivisionError
        ]
        for i in range(len(allExceptions)):
            if ec == allExceptions[i]:
                return i
        
        return 0xff

        
    @property
    def result_bytes(self):
        if not self.have_result:
            return bytearray(self.experiment.result_num_bytes)
            
        res = self.result 
            
        if isinstance(res, float):
            print(f'EXP RETURNING FLOAT RESULT {res}--intING!')
            res = int(res)
            
        if isinstance(res, int):
            try:
                return res.to_bytes(16, 'little')[:self.experiment.result_num_bytes]
            except:
                return bytearray('ieerror', 'ascii')[:self.experiment.result_num_bytes]
            
        if isinstance(res, str):
            try:
                return bytearray(res, 'utf-8')[:self.experiment.result_num_bytes]
            except:
                return bytearray('eerror', 'ascii')[:self.experiment.result_num_bytes]
            
        if isinstance(res, (bytearray, list)):
            return bytearray(res[:self.experiment.result_num_bytes])
            
    @property 
    def report(self):
        if self.have_exception:
            
            rep = bytearray([self.experiment.id, 0x80 | self.exception_type_id])
        else:
            rep = bytearray([self.experiment.id, 0]) 
            rep += self.result_bytes
        
        return rep
        
        
    def __repr__(self):
        completed = True 
        if self.have_exception:
            completed = False
        return f'<ExpResult {self.experiment.id} run {self.run_time}s, completed: {completed}, res: {self.result}>'
                
        

class ExperimentWatchdog:
    '''
        The ExperimentWatchdog is used to trigger experiment runs
        and collect results for reporting, while ensuring no 
        process can hang longer than its stated maximum duration.
        
        Because of the way uPython works, it doesn't seem possible 
        to interrupt a function from without, so the watchdog will 
        force the process to abort as required by monitoring runtime
        through a timer and, if necessary, log the failure and hard 
        reset the entire system.
    
    '''
    STARTUP=0
    IDLE=1
    WATCHING=2
    DONE=3
    TIMEDOUT=4
    def __init__(self, timer_period_ms=2000):
        
        if timer_period_ms > (SystemWatchdogTimerTimeoutMs / 2):
            print("Won't allow timer period more than half the WDT timeout")
            timer_period_ms = int(SystemWatchdogTimerTimeoutMs / 2)
        
        
        self.start_time = 0
        self.max_time = 0
        self.status = self.STARTUP
        self.timer_period_ms = timer_period_ms
        self.timer = Timer(-1)
        self.timer.init(period=self.timer_period_ms, mode=Timer.PERIODIC, callback=self._timer_callback)
        
        self.status = self.IDLE
        self.current_experiment = None
        self.wdt = WDT(timeout=SystemWatchdogTimerTimeoutMs)  

        
        
    def run(self, exp:Experiment):
        print(f'Running experiment {exp.id} (max duration {exp.timeout_s} secs)')
        self.current_experiment = exp
        self.start_time = time.time()
        self.max_time = self.start_time + exp.timeout_s
        experimentResult = ExperimentResult(exp, self.start_time)
        
        self.status = self.WATCHING
        try:
            experimentResult.result = exp.run()
            print(f'RES: {experimentResult.result}')
            experimentResult.run_completed = True
        except Exception as e:
            experimentResult.exception = e
            
        experimentResult.end_time = time.time()
        self.status = self.DONE
        
        return experimentResult
        
        
        
    def _timer_callback(self, timer):
        
        
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
        self.timer.deinit() # if reset somehow didn't work, WDT would do the job and finish us off
        self.timer = None
        time.sleep(3)
        reset()


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
    wd = ExperimentWatchdog()
    for ex in experiments:
        print(f'\n\nTriggering {ex}')
        eResult = wd.run(ex)
        print()
        print(eResult)
        print(f'Report: {eResult.report}')
        

if __name__ == '__main__':
    system_test()
    