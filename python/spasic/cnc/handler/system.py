'''
Created on Apr 21, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
from spasic.cnc.handler.base import HandlerBase
from spasic.cnc.command.system import SysCommand, Command
import spasic.cnc.command.system as scmd
import spasic.settings as sts
import spasic.cnc.response.response as rsp

class SysCmdHandler(HandlerBase):
    def __init__(self, coreSync, wdogAndRunner):
        super().__init__(coreSync, wdogAndRunner)
        
    def can_handle(self, cmd:Command):
        return isinstance(cmd, SysCommand)
    
    
    def handle(self, cmd:SysCommand):
        hndlmap = {
            scmd.Ping: self.handle_ping,
            scmd.Abort: self.handle_abort,
            scmd.RebootNormal: self.handle_reboot,
            scmd.RebootSafe: self.handle_reboot,
            scmd.SetSystemClock: self.handle_setsysclk
            }
        
        if type(cmd) in hndlmap:
            f = hndlmap[type(cmd)]
            return f(cmd)
        
        return False
        
    def handle_ping(self, cmd:scmd.Ping):
        self.respond(rsp.ResponseOKMessage(cmd.payload))
        return True 
    
    def handle_abort(self, cmd:scmd.Abort):
        return True 
    
    def handle_reboot(self, cmd:scmd.SysCommand):
        self.respond_ok()
        time.sleep(sts.RebootResponseDelaySeconds)
        self.reboot()
        return True
    
    def handle_setsysclk(self, cmd:scmd.SysCommand):
        return True 
    
    
        