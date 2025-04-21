'''

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.cnc.handler.base import HandlerBase
from spasic.cnc.command.command import Command
from spasic.cnc.handler.system import SysCmdHandler
from spasic.cnc.handler.schedule import ScheduleCmdHandler

class CommandHandler(HandlerBase):
    def __init__(self, wdogAndRunner):
        super().__init__(wdogAndRunner)
        self.sys_handler = SysCmdHandler(wdogAndRunner)
        self.sched_handler = ScheduleCmdHandler(wdogAndRunner)
    
    def handle(self, cmd:Command):
        
        if self.sys_handler.can_handle(cmd):
            return self.sys_handler.handle(cmd)
        
        if self.sched_handler.can_handle(cmd):
            return self.sched_handler.handle(cmd)
        
        return False