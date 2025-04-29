'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


import time
import _thread
from spasic.util.coresync import CoreSynchronizer
import spasic.settings as sts
from spasic.util.time import set_datetime
from spasic.i2c.device import I2CDevice
from spasic.i2c.parser import I2CInDataParser, i2cInDataReceived
from spasic.cnc.command.command import Command 
import spasic.cnc.command.schedule as cmd_sch
import spasic.cnc.command.system as cmd_sys
import spasic.cnc.response.response as rsp
import spasic.error_codes as error_codes

import spasic.experiment.tt_um_factory_test.loader as ldr

_thread.stack_size(8192)

def tx_done_cb():
    print('i2c tx done')
    
def tx_buffer_empty_cb():
    print('i2c buffer empty')


def timeset_cb(set_clk_cmd):
    # just setting it to epoch 0 + seconds elapsed
    # so... in the '70s
    set_datetime(*time.gmtime(set_clk_cmd.time))
    print(f'Time sync cmd: {set_clk_cmd}')

def queue_response(coreSync:CoreSynchronizer, resp:rsp.Response):
    coreSync.response_queue.put(resp)

class ExpResult:
    def __init__(self):
        self.result = bytearray()
        self.expid = 0
        self._completed = False 
        self.start_time = 0 
        self.end_time = 0
        self.success = False
        self._exception = None
        self._running = False
        
    def start(self):
        self.exception = None
        self.success = True
        self._completed = False
        self.start_time = time.time()
        self.end_time = 0
        self._running = True
        
    @property 
    def exception(self):
        return self._exception
    
    @exception.setter 
    def exception(self, set_to):
        self._exception = set_to 
        self._running = False
    
    @property 
    def running(self):
        return self._running
        
    @property 
    def run_duration(self):
        return self.end_time - self.start_time
        
    @property 
    def completed(self):
        return self._completed
    
    @completed.setter 
    def completed(self, set_to:bool):
        self._completed = set_to
        if set_to:
            self.end_time = time.time()
            self._running = False
            
    
    def __str__(self):
        return f'Exp {self.expid} [{self._completed} {self.run_duration}s]: {self.result}>'
            
        

ERes = ExpResult()
def handle_command(coreSync:CoreSynchronizer, cmd:Command):
    if isinstance(cmd, cmd_sch.RunImmediate):
        print("Run experiment")
        
        if ERes.running:
            queue_response(coreSync, rsp.ResponseError(error_codes.Busy, 
                                                       ERes.expid.to_bytes(2, 'little')))
            return 
        
        
        
        
        ERes.expid = cmd.experiment_id
        ERes.start()
        _thread.start_new_thread(ldr.run_experiment, (ERes,))
        
        respmsg = b'EXP'
        respmsg += cmd.experiment_id.to_bytes(2, 'little')
        queue_response(coreSync, rsp.ResponseOKMessage(respmsg))
        
        
    elif isinstance(cmd, cmd_sys.Ping):
        print("Ping")
        print(ERes)
        queue_response(coreSync, rsp.ResponseOKMessage(cmd.payload))
    elif isinstance(cmd, cmd_sys.Status):
        print("Status")
        queue_response(coreSync, rsp.ResponseOK())
    elif isinstance(cmd, (cmd_sys.RebootNormal, cmd_sys.RebootSafe)):
        print("Reboot")
        queue_response(coreSync, rsp.ResponseOK())
    elif isinstance(cmd, cmd_sys.SetSystemClock):
        print("Set Clock")
        queue_response(coreSync, rsp.ResponseOK())
    else:
        print("Unknown/unhandled command")

def get_data_parser(coreSync:CoreSynchronizer):
    in_data_parser = I2CInDataParser(coreSync)
    in_data_parser.time_set_callback = timeset_cb
    return in_data_parser

def get_i2c_device():
    # create our slave device
    i2c_dev = I2CDevice(address=sts.DeviceAddress, scl=sts.I2CSCL, sda=sts.I2CSDA,
                        baudrate=sts.I2CBaudRate)
    
    return i2c_dev

def main_loop():
    print("Entering main loop")
    coreSync = CoreSynchronizer()
    # create something that can grok what comes over the channel
    # and can respond appropriately
    in_data_parser = get_data_parser(coreSync)
    i2c_dev = get_i2c_device()
    # setup the callbacks
    i2c_dev.callback_data_in = i2cInDataReceived
    i2c_dev.callback_tx_done = tx_done_cb 
    i2c_dev.callback_tx_buffer_empty = tx_buffer_empty_cb
    
    # init the i2c device and start listening
    print("Starting i2c device:")
    if i2c_dev.begin():
        print("  success")
    else:
        print("  already init?")
    
    loop_count = 0
    while True:
        try:
            
            # may have queued data received from 
            # master side, process that into commands
            print(".", end='')
            i2c_dev.poll_pending_data()
            num_incoming = in_data_parser.process_pending_data()
            loop_count += 1
            if num_incoming > 0 or loop_count % 50 == 0:
                print(f'\nIn: {num_incoming}')
            while not coreSync.command_queue.empty():
                cmd = coreSync.command_queue.get()
                print(cmd)
                handle_command(coreSync, cmd)
                
            out_data = bytearray()
            while not coreSync.response_queue.empty():
                rsp = coreSync.response_queue.get()
                print(rsp)
                out_data += rsp.bytes
            
            if len(out_data):
                print(f"Have data to send: {out_data}")
                i2c_dev.queue_outdata(out_data)
                
            i2c_dev.push_outgoing_data()
                
            time.sleep_ms(5)
                
        except Exception as e:
            print(f'ml ex: {e}')
            raise e
    



#def server_launch(coreSync:CoreSynchronizer):
#    _thread.start_new_thread(main_loop, (coreSync, ))

#def server_teardown():
#    global ContinueHandling
#    ContinueHandling = False




def simple_run():
    c = CoreSynchronizer()
    main_loop(c)
    

if __name__ == '__main__':
    simple_run()


    




