'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

from spasic.cnc.command.command import Command

class SysCommand(Command):
    pass 

class Ping(SysCommand):
    def __init__(self, bts:bytearray):
        super().__init__()
        self.payload = bts
        
class Status(SysCommand):
    def __init__(self):
        pass

class RebootSafe(SysCommand):
    pass

class RebootNormal(SysCommand):
    pass

class SetSystemClock(SysCommand):
    def __init__(self, bts:bytearray):
        super().__init__()
        self.time = 0
        if bts is not None and len(bts) >= 4:
            try:
                self.time = int.from_bytes(bts, 'little')
            except:
                print(f"BAD time sent? {bts}")
                
        

    def __repr__(self):
        return f'<SetSystemClock {self.time}>'

    def __str__(self):
        return f'SetSystemClock: {self.time}'


class Abort(SysCommand):
    pass