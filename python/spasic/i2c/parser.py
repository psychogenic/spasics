'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
from spasic.util.coresync import CoreSynchronizer
import spasic.cnc.command.system as cmd_sys
import spasic.cnc.command.schedule as cmd_sch
import spasic.cnc.response.response as rsp
import spasic.error_codes as err_codes
from spasic.util.queue import Queue

class I2CInDataParser:
    
    def __init__(self, coresync:CoreSynchronizer):
        self._core_sync = coresync
        self.time_set_callback = None
        self._pending_in_data = [] # Queue()
        
    @property 
    def core_sync(self):
        return self._core_sync
    
    def data_receivedNEW(self, numbytes:int, bts:bytearray):
        print(f"PARSER DATA IN: {bts}")
        if not numbytes or not len(bts):
            return 
        self.core_sync.lock.acquire()
        self._pending_in_data.append(bytearray(bts))
        self.core_sync.lock.release()
        
        # self._pending_in_data.put(deepcpy)
        
    def process_pending_data(self):
        if True:
            return
        message_map = {
            ord('E'): self.handle_run_experiment,
            ord('P'): self.handle_ping,
            ord('R'): self.handle_reboot,
            ord('T'): self.handle_set_sysclock,
            
            }
        
        self.core_sync.lock.acquire()
        if not len(self._pending_in_data):
            self.core_sync.lock.release()
            return 
        # bts = self._pending_in_data.get(block=False)
        
        for bts in self._pending_in_data:
            print(f"HAD PND {bts}")
            if bts[0] in message_map:
                f = message_map[bts[0]]
                print(f"F IS {f}")
                f(bts[1:])
            else:
                self.core_sync.response_queue.put(rsp.ResponseError(err_codes.UnknownCommand, bts))
            # bts = self._pending_in_data.get(block=False)
        
        self.core_sync.lock.release()
        
        
    
    def data_received(self, numbytes:int, bts:bytearray):
        print(f"PARSER DATA IN: {bts}")
        if not numbytes or not len(bts):
            return 
        
        message_map = {
            ord('E'): self.handle_run_experiment,
            ord('P'): self.handle_ping,
            ord('R'): self.handle_reboot,
            ord('T'): self.handle_set_sysclock,
            
            }
        
        if bts is not None:
            if bts[0] in message_map:
                f = message_map[bts[0]]
                f(bts[1:])
            else:
                self.core_sync.response_queue.put(rsp.ResponseError(err_codes.UnknownCommand, bts))
            
        
    def handle_set_sysclock(self, payload:bytearray):
        set_clk_cmd = cmd_sys.SetSystemClock(payload)
        self.core_sync.command_queue.put(set_clk_cmd)
        if self.time_set_callback is not None:
            self.time_set_callback(set_clk_cmd)
                
             
    def handle_ping(self, payload:bytearray):
        self.core_sync.command_queue.put(cmd_sys.Ping(payload))
    def handle_run_experiment(self, payload:bytearray):
        if payload is not None and len(payload):
            exp_id = int.from_bytes(payload, 'little')
        else:
            exp_id = 0
        self.core_sync.command_queue.put(cmd_sch.RunImmediate(exp_id))
        
    def handle_reboot(self, payload:bytearray):
        if len(payload) and payload[0]:
            self.core_sync.command_queue.put(cmd_sys.RebootSafe())
        else:
            self.core_sync.command_queue.put(cmd_sys.RebootNormal())
        return True
            
            