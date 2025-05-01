'''
Created on May 1, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
class Variables:
    def __init__(self):
        self._vars = dict()
        self.set_string(1, 'TEST: this is a test of my very fine friend oh yes indeed sir my good sir')
        
    def clear(self):
        self._vars = dict()
        
    def has(self, vid:int):
        return vid in self._vars
    
    def get(self, vid:int):
        if not self.has(vid):
            return None 
        return self._vars[vid]
    
    def get_bytearray(self, vid:int):
        if not self.has(vid):
            return bytearray() 
        v = self.get(vid)
        if isinstance(v, str):
            try:
                return bytearray(v, 'ascii')
            except:
                print(f"NON-ascii str?? {v}")
                return bytearray('BADSTR', 'ascii')
        if isinstance(v, int):
            return v.to_bytes(4, 'little')
        return v
        
    
    def get_string(self, vid:int):
        if not self.has(vid):
            return ''
        v = self.get(vid)
        if isinstance(v, str):
            return v 
        if isinstance(v, (bytes, bytearray)):
            return v.decode('ascii')
        return str(v)

    def set(self, vid:int, val):
        self._vars[vid] = val 
        
    def append(self, vid:int, val):
        if not self.has(vid):
            return False 
        
        self._vars[vid] += val
    
    def set_string(self, vid:int, val:str):
        self.set(vid, '')
        return self.append_string(vid, val)
    
    def append_string(self, vid:int, val:str):
        if not self.has(vid):
            return False
        if isinstance(val, (bytes, bytearray)):
            try:
                sval = val.decode('ascii')
            except:
                return False
        elif isinstance(val, str):
            sval = val
        else:
            return False
        
            
        self._vars[vid] += sval