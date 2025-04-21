'''

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


class ExperimentResponse:
    '''
        An experiment response holds the result reported by an experimental run.
    '''
    def __init__(self):
        self.result = None
    
    
    @property
    def have_result(self):
        return self.result is not None
        

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
        
    def run(self, intermediateResponse:ExperimentResponse):
        f = self.func 
        return f(intermediateResponse)
        
    def __repr__(self):
        return f'<Experiment {self.id}>'
    
    
        
class ExperimentResult(ExperimentResponse):
    '''
        An ExperimentResult holds the details of an experimental run.
        It knows when the experiment was started, which experiment it 
        is related to, and can return results or exceptions in a manner
        suitable for reporting.
    '''
    def __init__(self, experiment:Experiment, 
                start_time_s:int):
        super().__init__()
        self.experiment = experiment
        self.start_time = start_time_s
        self.run_completed = False
        self.end_time = 0
        self.exception = None 
        
    @property
    def run_time(self):
        if self.end_time == 0:
            return 0
            
        return self.end_time - self.start_time
        
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
                
        