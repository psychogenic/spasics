'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

from spasic.cnc.command.command import Command

class SysCommand(Command):
    pass 

class HeartBeat(SysCommand):
    pass

class RebootSafe(SysCommand):
    pass

class RebootNormal(SysCommand):
    pass

class SetSystemClock(SysCommand):
    pass

class Abort(SysCommand):
    pass