'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
'''
    Copyright (C) 2025 Pat Deegan, https://psychogenic.com
    
    Simple example of an implementation class that lets you
    * configure callbacks for async events from i2c
    
    * setup the i2c slave, using begin
    
    * call queue_data() as much as you like for outgoing
    
    * get a callback triggered for all incoming, every tx of a blob
      and whenever the tx buffer goes empty

'''

import time
SlaveAddressDefault = 0x51
DefaultBaudRate = 100000


try:
    import i2cslave
except:
    print("\n\n\nERROR: Not running uPython w/i2cslave support!\n\n")

HavePendingDataIn = False
class I2CDevice:
    '''
        Construct the device,
        Set
            dev.callback_data_in = somefunc taking NUMBYTES, BYTES parms
            dev.callback_tx_done = signal for blob sent
            dev.callback_tx_buffer_empty = signal for nothing at all left in tx queue
            
        Call begin() and check it returns True
        
        Do whatever you like in the meantime
    
    '''
    SlaveBufferSize = 16*7
    
    def __init__(self, address:int=SlaveAddressDefault, 
                 scl:int=3, 
                 sda:int=2, baudrate:int=DefaultBaudRate):
        self._addr = address 
        self._scl = scl 
        self._sda = sda 
        self._baud = baudrate
        self._dataqueue = bytearray()
        self._slavebuf_filled = False
        
        self.callback_data_in = None
        self.callback_tx_done = None 
        self.callback_tx_buffer_empty = None 
        # self._have_pending = False
        self._data_xfer_done = False
        self._scratch_buf = bytearray(32)
        self._scratch_size = 0
        
        
    def data_receivedOLD(self, numbytes:int, bts:bytearray):
        if self.callback_data_in is not None:
            self.callback_data_in(numbytes, bts)
            return 
        
        print(f'Data in: {bts}')
    
    def data_received(self, _sz:int):
        global HavePendingDataIn
        HavePendingDataIn = True
        
    def poll_pending_data(self):
        global HavePendingDataIn
        if not HavePendingDataIn: # self._have_pending:
            return
        
        HavePendingDataIn = False # handled
        
        if self.callback_data_in is not None:
            print("Getting pending")
            # doing a whole dance here, for nothing...
            # bts = bytearray(16)
            self._scratch_size = int(i2cslave.pending_data_into(self._scratch_buf))
            #self._scratch_buf = bytearray(bts)
            print(f"GOT {self._scratch_buf[:self._scratch_size]}, doing cb")
            self.callback_data_in(self._scratch_size, self._scratch_buf[:self._scratch_size])
            print("DONO")
            
        
    def _write_outbytes(self):
        if self._slavebuf_filled or not len(self._dataqueue):
            return 0
        # 
        if len(self._dataqueue) > self.SlaveBufferSize:
            to_send = self._dataqueue[:self.SlaveBufferSize]
            self._dataqueue = self._dataqueue[self.SlaveBufferSize:]
        else:
            to_send = self._dataqueue
            self._dataqueue = bytearray()
            
        i2cslave.write_bytes(len(to_send), to_send)
        self._slavebuf_filled = True
        return len(to_send)
        
    def queue_outdata(self, data_out:bytearray):
        self._dataqueue += data_out
        if not len(self._dataqueue):
            return 
            
        self._write_outbytes()
        
    
    def _data_tx_done_cb(self, _unused=None):
        self._data_xfer_done = True 
        
    def push_outgoing_data(self):
        if not self._data_xfer_done:
            return 
        
        self._data_xfer_done = False
        self._slavebuf_filled = False
        if self.callback_tx_done is not None:
            print(f"tx done cb: {self.callback_tx_done}")
            self.callback_tx_done()
            
        if not self._write_outbytes():
            if self.callback_tx_buffer_empty is not None:
                print(f"tx empty cb {self.callback_tx_buffer_empty}")
                self.callback_tx_buffer_empty()
                
        
        
        
    def begin(self):
        i2cslave.setup(self._addr, self._scl, self._sda, self._baud) 
        i2cslave.set_datain_callback(self.data_received)
        i2cslave.set_datatxdone_callback(self._data_tx_done_cb)
        try:
            i2cslave.initialize()
        except:
            print("i2c slave init failed!")
            return False 
            
        return True
    

# start_i2c()
