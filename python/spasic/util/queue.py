'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import _thread
import time

SpinLockSleepTimeMs = 2
RaiseErrors = False


class QueueFull(Exception):
    pass 
class QueueEmpty(Exception):
    pass 

class Queue:
    def __init__(self, maxsize:int=0):
        self._max_size = maxsize 
        self._q = []
        self._lock = _thread.allocate_lock()
    
    def lock(self):
        pass # self._lock.acquire()
    def release(self):
        pass # self._lock.release()
        
    def qsize(self):
        self.lock()
        l = len(self._q)
        self.release()
        
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
            if SpinLockSleepTimeMs > 0:
                time.sleep_ms(SpinLockSleepTimeMs)
            if not block:
                if RaiseErrors:
                    raise QueueFull("q full,noblk")
                return False
            
            
        self.lock()
        self._q.append(item)
        self.release()
        
    def get(self, block=True):
        
        while self.empty():
            if SpinLockSleepTimeMs > 0:
                time.sleep_ms(SpinLockSleepTimeMs)
            if not block:
                if RaiseErrors:
                    raise QueueEmpty("q empty,noblk")
                return None
            
        
        self.lock()
        ritem = self._q[0]
        if len(self._q) < 2:
            self._q = []
        else:
            self._q = self._q[1:]
        self.release()
        return ritem
        
        
            
        
