'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import os

class FSAccess:
    
    def __init__(self):
        self._fh = None 
    
    def file_size(self, filename):
        try:
            st = os.stat(filename)
            return st[6]
        except Exception as _e:
            return 0xffffff
        
    def exists(self, filepath):
        try:
            os.stat(filepath)
        except:
            return False 
        
        return True
    
    def delete(self, filepath):
        try:
            os.remove(filepath)
        except:
            return False 
        
        return True
    def move(self, oldpath, newpath):
        try:
            os.rename(oldpath, newpath)
        except:
            return False 
        return True
    def lsdir(self, path):
        try:
            dirs = os.listdir(path)
        except:
            return ''
        
        return '|'.join(dirs)
    def mkdir(self, path):
        if not len(path):
            print("No path passed?")
            return False 
        
        if path[0] != '/':
            print("Use full path")
            return False 
    
        comps = path.split('/')
        curdirs = ['']
        for sdir in comps:
            if not len(sdir):
                continue 
            curdirs.append(sdir)
            cdir = '/'.join(curdirs)
            try:
                os.stat(cdir)
            except:
                # DNE
                os.mkdir(cdir)
                
        return self.exists(path)
                    
        
    def close(self):
        if self._fh is None:
            return False 
        
        self._fh.close()
        self._fh = None 
        return True
    def simple_checksum(self, filepath):
        if not self.open_for_read(filepath):
            return 0xffffff
        
        csum = 0
        v = self.read_bytes(4)
        while len(v):
            nval = int.from_bytes(v, 'little')
            csum = csum ^ nval
            v = self.read_bytes(4)
            
        return csum
        
    def open_for_read(self, filepath:str):
        if self._fh is not None:
            self._fh.close()
        try:
            self._fh = open(filepath, 'rb')
        except:
            return False
        
        return True
    
    def read_bytes(self, sz:int=16):
        if self._fh is None:
            return bytearray()
        bts = self._fh.read(sz)
        if not len(bts):
            self._fh.close()
            self._fh = None 
        
        return bts
    
    def open_for_write(self, filepath:str):
        if self._fh is not None:
            self._fh.close()
        try:
            self._fh = open(filepath, 'wb')
        except:
            return False
        
        return True
    def write_bytes(self, bts:bytearray):
        if self._fh is None:
            return False 
        
        return self._fh.write(bts)
    