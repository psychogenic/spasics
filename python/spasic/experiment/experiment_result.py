'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time

class ExpResult:
    def __init__(self):
        self.result = bytearray()
        self.expid = 0
        self._completed = False 
        self.start_time = 0 
        self.end_time = 0
        self.success = False
        self._exception = None
        self._running = False
        
    def start(self):
        self.exception = None
        self.success = True
        self._completed = False
        self.start_time = time.time()
        self.end_time = 0
        self._running = True
        
    @property 
    def exception(self):
        return self._exception
    
    @exception.setter 
    def exception(self, set_to):
        self._exception = set_to 
        self._running = False
        self.end_time = time.time()
    
    @property 
    def running(self):
        if self._exception is not None:
            return False
        return self._running
        
    @property 
    def run_duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
        
    @property 
    def completed(self):
        return self._completed
    
    @completed.setter 
    def completed(self, set_to:bool):
        self._completed = set_to
        if set_to:
            self.end_time = time.time()
            self._running = False
            
    @classmethod 
    def exception_to_id(cls, ex:Exception):
        
        if not hasattr(ex, '__class__'):
            return 0xfe 
            
        ec = ex.__class__ 
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
                return i + 1
        
        return 0xff
    
    @property 
    def exception_type_id(self):
        if not self._exception:
            return 0 
        
        return self.exception_to_id(self._exception)
    
    def __str__(self):
        return f'Exp {self.expid} [{self._completed} {self.run_duration}s]: {self.result}>'
            