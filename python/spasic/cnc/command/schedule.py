'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

from spasic.cnc.command.command import Command

class ScheduleCommand(Command):
    pass 

class RunImmediate(ScheduleCommand):
    def __init__(self, experiment_id:int):
        self.experiment_id = experiment_id
        
    
    def __repr__(self):
        return f'<RunImmediate for {self.experiment_id}>'
    
