'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import _thread
import time

SpinLockSleepTimeMs = 2



class QueueFull(Exception):
    pass 
class QueueEmpty(Exception):
    pass 

class Queue:
    def __init__(self, maxsize:int=0):
        self._max_size = maxsize 
        self._q = []
        self.lock = _thread.allocate_lock()
        
    def qsize(self):
        self.lock.acquire()
        l = len(self._q)
        self.lock.release()
        
        return l 
    
    def empty(self):
        return self.qsize() == 0
    
    def full(self):
        if self._max_size < 1:
            return False 
        
        sz = self.qsize()
        return sz < self._max_size
    
    def put(self, item, block=True):
        
        while self.full():
            if not block:
                raise QueueFull("q full,noblk")
            if SpinLockSleepTimeMs > 0:
                time.sleep_ms(SpinLockSleepTimeMs)
            
        self.lock.acquire()
        self._q.append(item)
        self.lock.release()
        
    def get(self, block=True):
        
        while self.empty():
            if not block:
                raise QueueEmpty("q empty,noblk")
            if SpinLockSleepTimeMs > 0:
                time.sleep_ms(SpinLockSleepTimeMs)
            
        
        self.lock.acquire()
        ritem = self._q[0]
        if len(self._q) < 2:
            self._q = []
        else:
            self._q = self._q[1:]
        self.lock.release()
        return ritem
        
        
            
        
