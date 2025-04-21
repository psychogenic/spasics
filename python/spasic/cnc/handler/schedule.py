'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


from spasic.cnc.handler.base import HandlerBase
from spasic.cnc.command.schedule import ScheduleCommand, Command
import spasic.cnc.command.schedule as schcmd

class ScheduleCmdHandler(HandlerBase):
    def __init__(self, wdogAndRunner):
        super().__init__(wdogAndRunner)
        
    def can_handle(self, cmd:Command):
        return isinstance(cmd, ScheduleCommand)
    
    
    def handle(self, cmd:ScheduleCommand):
        hndlmap = {
            schcmd.RunImmediate: self.handle_runimmediate,
            }
        
        if type(cmd) in hndlmap:
            f = hndlmap[type(cmd)]
            return f(cmd)
        
        return False
        
    def handle_runimmediate(self, cmd:schcmd.RunImmediate):
        print(f'Running {cmd.experiment}')
        experimentVal = self.run(cmd.experiment)
        print(f'Done')
        print(experimentVal)
        return True 
    