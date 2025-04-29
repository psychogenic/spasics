'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
from spasic.util.coresync import CoreSynchronizer
import spasic.cnc.command.system as cmd_sys
import spasic.cnc.command.schedule as cmd_sch
import spasic.cnc.response.response as rsp
import spasic.error_codes as err_codes
from spasic.util.queue import Queue

_DataParserSingleTon = None 
def i2cInDataReceived(numbytes:int, bts:bytearray):
    print(f"IN {bts}")
    I2CInDataParser.get().data_received(numbytes, bts)


class I2CInDataParser:
    
    @classmethod 
    def get(cls):
        global _DataParserSingleTon
        return _DataParserSingleTon
    
    def __init__(self, coresync:CoreSynchronizer):
        global _DataParserSingleTon
        self._core_sync = coresync
        self.time_set_callback = None
        self._pending_in_data = [] # Queue()
        self.msg_handle_map = {
            ord('E'): self.handle_run_experiment,
            ord('P'): self.handle_ping,
            ord('R'): self.handle_reboot,
            ord('S'): self.handle_get_status,
            ord('T'): self.handle_set_sysclock,
            
            }
        if _DataParserSingleTon is not None:
            raise RuntimeError("Only construct one of these")
        
        _DataParserSingleTon = self
        
    
    @property 
    def core_sync(self):
        return self._core_sync
    
    def lock(self):
        pass # self.core_sync.lock.acquire()
    def release(self):
        pass # self.core_sync.lock.release()
        
    def throttle(self):
        time.sleep_ms(10)
        
    def data_received(self, numbytes:int, bts:bytearray):
        if not numbytes or not len(bts):
            print("DR with no dat?")
            return 
        self.lock()
        self._pending_in_data.append(bts)
        print(self._pending_in_data)
        self.release()
        
        # self._pending_in_data.put(deepcpy)
        
    def process_pending_data(self): 
        self.throttle()
        if not len(self._pending_in_data):
            return 0
        self.lock()
        # copy
        pending_dat = list(self._pending_in_data)
        # empty
        self._pending_in_data[:] = []
        
        self.release()
        self.throttle()
        
        num_msgs = 0
        # bts = self._pending_in_data.get(block=False)
        
        for hotdata in pending_dat:
            bts = bytearray(hotdata)
            # print(f"HAD PND {bts}")
            self.throttle()
            num_msgs += 1
            first_byte = bts[0]
            print(f'MSG type: {first_byte}')
            if first_byte in self.msg_handle_map:
                f = self.msg_handle_map[first_byte]
                print(f"F IS {f}")
                self.throttle()
                f(bts[1:])
                print("F done")
            else:
                print("Unknown message!")
                self.throttle()
                self.core_sync.response_queue.put(rsp.ResponseError(err_codes.UnknownCommand, bts))
                self.throttle()
            # bts = self._pending_in_data.get(block=False)
        
        return num_msgs
        
    
        
    def handle_get_status(self, payload:bytearray):
        self.core_sync.command_queue.put(cmd_sys.Status())
        
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
            
            