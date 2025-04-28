'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


import time
import _thread
from spasic.util.coresync import CoreSynchronizer
import spasic.settings as sts
from spasic.util.time import set_datetime





def tx_done_cb():
    print('i2c tx done')
    
def tx_buffer_empty_cb():
    print('i2c buffer empty')


def timeset_cb(set_clk_cmd):
    # just setting it to epoch 0 + seconds elapsed
    # so... in the '70s
    set_datetime(*time.gmtime(set_clk_cmd.time))
    print(f'Time sync cmd: {set_clk_cmd}')


def data_parser(sync:CoreSynchronizer):
    
    from spasic.i2c.parser import I2CInDataParser
    in_data_parser = I2CInDataParser(sync)
    in_data_parser.time_set_callback = timeset_cb
    
    return in_data_parser

def main_loop(sync:CoreSynchronizer):
    from spasic.i2c.device import I2CDevice
    
    # create our slave device
    i2c_dev = I2CDevice(address=sts.DeviceAddress, scl=sts.I2CSCL, sda=sts.I2CSDA,
                        baudrate=sts.I2CBaudRate)
    
    # create something that can grok what comes over the channel
    # and can respond appropriately
    in_data_parser = data_parser(sync)
    
    # setup the callbacks
    i2c_dev.callback_data_in = in_data_parser.data_received
    i2c_dev.callback_tx_done = tx_done_cb 
    i2c_dev.callback_tx_buffer_empty = tx_buffer_empty_cb
    
    # init the i2c device and start listening
    i2c_dev.begin()
    
    while True:
        try:
            in_data_parser.process_pending_data()
            rsp = sync.response_queue.get(False)
            if rsp is None:
                time.sleep(0.01)
            else:
                print(f'q resp')
                i2c_dev.queue_outdata(rsp.bytes)
        except Exception as e:
            print(f'ml excep: {e}')
    



def server_launch(coreSync:CoreSynchronizer):
    _thread.start_new_thread(main_loop, (coreSync, ))

def server_teardown():
    global ContinueHandling
    ContinueHandling = False




def simple_run():
    c = CoreSynchronizer()
    main_loop(c)
    

if __name__ == '__main__':
    simple_run()


    




