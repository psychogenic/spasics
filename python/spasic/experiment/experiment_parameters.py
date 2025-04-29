'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from ttboard.demoboard import DemoBoard
class ExperimentParameters:
    def __init__(self, tt_db:DemoBoard):
        self.tt = tt_db 
        self._keep_running = False 
        self.argument_bytes = bytearray(10)
        
    @property 
    def keep_running(self):
        return self._keep_running 
    
    def start(self, args:bytearray=None):
        self._keep_running = True 
        if args is None:
            self.argument_bytes = bytearray(10)
        else:
            self.argument_bytes = args
    def terminate(self):
        self._keep_running = False 
        
        
