'''

Synchronization/communication between cores all through instance 
of this class.

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import _thread
from spasic.util.queue import Queue

class CoreSynchronizer:
    
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.command_queue = Queue()
        
        
        
        
        