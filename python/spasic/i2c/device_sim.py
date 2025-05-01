'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
###
### REPL test without actual I2C master in the game
### To use, 
###  1) load I2CDevice from here
###  2) use I2CDevice class' augmented
###      sim_data_received and 
###      sim_master_data_request
###     methods
###
### The idea is to copy the device.py I2CDevice class
### AS-IS and add those two methods, all the magic 
### happens in the SlaveSim instance, which replaces
### the i2cslave module.
###
### Then, launch i2c_server.main_loop in a thread, get_i2c_device and
### play with sending data and reading bytes
### 
### d = i2c_server.get_i2c_device()
### for i in range(16):
###     d.sim_data_received(bytearray([ord('P'), i, ord('P'), ord('N'), ord('G')]))
###     time.sleep(0.02) # important
###
### Then do a bunch of d.sim_master_data_request() to see what got queued back

class SlaveSim:
    def __init__(self):
        self.addr = 0 
        self.scl = 0 
        self.sda = 0 
        self.freq = 0
        self._din_cb = None 
        self._txdone_cb = None
        self._data_in = bytearray()
        self._data_out = bytearray()
         
    def setup(self, addr:int, scl:int, sda:int, baud:int=100000):
        self.addr = addr 
        self.scl = scl 
        self.sda = sda 
        self.freq = baud 
        
        
    def set_datain_callback(self, cb):
        self._din_cb = cb 
    def set_datatxdone_callback(self, cb):
        self._txdone_cb = cb 
        
    def initialize(self):
        return 
    def pending_data_into(self, bts:bytearray):
        bsize = len(bts)
        for i in range(bsize):
            bts[i] = 0xff 
        
        if len(self._data_in) >= bsize:
            cplen = bsize
        else:
            cplen = len(self._data_in)
        
        for i in range(cplen):
            bts[i] = self._data_in[i]
            
        if cplen:
            self._data_in = self._data_in[cplen:]
            
        return cplen
    
    def write_bytes(self, sz:int, bts:bytearray):
        self._data_out = bytearray(bts[:sz]) # local copy
    
    def master_send_data(self, bts:bytearray):
        self._data_in += bts 
        cb = self._din_cb
        if cb is not None:
            cb(len(bts))
            
    def master_request_data(self):
        ret_data = bytearray([0xff]*16)
        doutsz = len(self._data_out)
        if doutsz:
            cplen = 16
            if cplen > doutsz:
                cplen = doutsz 
            
            for i in range(cplen):
                ret_data[i] = self._data_out[i]
            
            self._data_out = self._data_out[cplen:]
            
        if not len(self._data_out):
            cb = self._txdone_cb
            if cb is not None:
                cb(None)
                
        return ret_data
            
i2cslave = SlaveSim()


          

SlaveAddressDefault = 0x51
DefaultBaudRate = 100000  

HavePendingDataIn = False
class I2CDevice:
    #
    # Construct the device,
    # Set
    #     dev.callback_data_in = somefunc taking NUMBYTES, BYTES parms
    #     dev.callback_tx_done = signal for blob sent
    #     dev.callback_tx_buffer_empty = signal for nothing at all left in tx queue
    #
    # Call begin() and check it returns True
    #
    # Do whatever you like in the meantime
    #
    #

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
    
    
    
    def sim_data_received(self, data:bytearray):
        i2cslave.master_send_data(data)
        
    def sim_master_data_request(self):
        return i2cslave.master_request_data()
        
    def sim_master_data_all(self):
        empty = bytearray([0xff]*16)
        v = i2cslave.master_request_data()
        retBts = []
        while v != empty:
            retBts.append(v)
            v = i2cslave.master_request_data()
        
        return retBts
            
            
    
    
    
    
    def data_received(self, _sz:int):
        global HavePendingDataIn
        HavePendingDataIn = True
        
    def poll_pending_data(self):
        global HavePendingDataIn
        if not HavePendingDataIn: # self._have_pending:
            return
        
        HavePendingDataIn = False # handled
        
        if self.callback_data_in is not None:
            self._scratch_size = int(i2cslave.pending_data_into(self._scratch_buf))
            # print(f"GOT {self._scratch_buf[:self._scratch_size]}, doing cb")
            self.callback_data_in(self._scratch_size, self._scratch_buf[:self._scratch_size])
            
    @property 
    def outdata_queue_size(self):
        return len(self._dataqueue)
    
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
            # print(f"tx done cb: {self.callback_tx_done}")
            self.callback_tx_done()
            
        if not self._write_outbytes():
            if self.callback_tx_buffer_empty is not None:
                # print(f"tx empty cb {self.callback_tx_buffer_empty}")
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
    
