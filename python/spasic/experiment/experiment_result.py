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
    
    @property 
    def running(self):
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
            
    
    def __str__(self):
        return f'Exp {self.expid} [{self._completed} {self.run_duration}s]: {self.result}>'
            