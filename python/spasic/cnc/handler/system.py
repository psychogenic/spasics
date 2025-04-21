'''
Created on Apr 21, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.cnc.handler.base import HandlerBase
from spasic.cnc.command.system import SysCommand, Command
import spasic.cnc.command.system as scmd
class SysCmdHandler(HandlerBase):
    def __init__(self, wdogAndRunner):
        super().__init__(wdogAndRunner)
        
    def can_handle(self, cmd:Command):
        return isinstance(cmd, SysCommand)
    
    
    def handle(self, cmd:SysCommand):
        hndlmap = {
            scmd.HeartBeat: self.handle_heartbeat,
            scmd.Abort: self.handle_abort,
            scmd.RebootNormal: self.handle_reboot,
            scmd.RebootSafe: self.handle_reboot,
            scmd.SetSystemClock: self.handle_setsysclk
            }
        
        if type(cmd) in hndlmap:
            f = hndlmap[type(cmd)]
            return f(cmd)
        
        return False
        
    def handle_heartbeat(self, cmd:scmd.HeartBeat):
        return True 
    
    def handle_abort(self, cmd:scmd.Abort):
        return True 
    def handle_reboot(self, cmd:scmd.SysCommand):
        self.reboot()
    
    def handle_setsysclk(self, cmd:scmd.SysCommand):
        return True 