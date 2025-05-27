'''
Created on May 5, 2025

@author: Michael Bell
@copyright: Copyright (C) 2025 Michael Bell
'''
import time
import rp2
import machine
from machine import Pin
from micropython import const
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters
import ttboard.util.platform as platform

FLASH_CS = const(0)
SD0 = const(1)
SD1 = const(2)
SCK = const(3)
SD2 = const(4)
SD3 = const(5)
RAM_CS = const(6)

@rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_LEFT, in_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=8, out_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW, rp2.PIO.IN_LOW, rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW))
def pio_write_data():
    out(isr, 2)
    in_(null, 1)
    out(x, 2)
    in_(x, 2)
    wait(0, gpio, 24)
    mov(pins, isr)
    wait(1, gpio, 24)
    
@rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_LEFT, in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=24)
def pio_read_addr():
    wait(1, gpio, 24)
    mov(osr, pins)
    out(x, 2)
    in_(x, 2)
    out(null, 1)
    out(x, 2)
    in_(x, 2)
    wait(0, gpio, 24)

@micropython.native
def read_raw_nibble():
    b = platform.read_uio_byte()
    return ((b >> 1) & 0b0011) | ((b >> 2) & 0b1100)

@micropython.viper
def toggle_clock():
    machine.mem32[0xd000001c] = 1
    machine.mem32[0xd000001c] = 1

@micropython.viper
def run_cycles(clocks:int, cur_sck:int) -> int:
    while clocks > 0:
        val = int(machine.mem32[0xd0000004]) >> 21
        if val & 1: break
        new_sck = (val & 8)
        if new_sck != cur_sck:
            cur_sck = new_sck
            clocks -= 1
        machine.mem32[0xd000001c] = 1
        machine.mem32[0xd000001c] = 1
        
    return clocks

@micropython.viper
def clock_out_data() -> int:
    clocks = 0
    cur_sck = 0
    while True:
        val = int(machine.mem32[0xd0000004]) >> 21
        if val & 1: break
        new_sck = (val & 8)
        if new_sck != cur_sck:
            cur_sck = new_sck
            clocks += 1
        machine.mem32[0xd000001c] = 1
        machine.mem32[0xd000001c] = 1
        
    return clocks // 4

class TinyQV:
    def __init__(self, tt):
        tt.shuttle.tt_um_MichaelBell_tinyQV.enable()
        tt.clock_project_stop()

        tt.clk.off()
        tt.reset_project(False)
        tt.clock_project_once()
        tt.clock_project_once()
        tt.reset_project(True)
        tt.clk.off()
        
        tt.clk.on()
        time.sleep(0.001)
        tt.clk.off()
        time.sleep(0.001)

        # Set inputs - UART RX high
        tt.ui_in.value = 0x80

        # Set QSPI latency to 1.
        tt.uio_in.value = 2
        try:
            tt.uio_oe_pico.value = 0xff

            for i in range(10):
                tt.clk.off()
                time.sleep(0.001)
                tt.clk.on()
                time.sleep(0.001)
        finally:
            tt.uio_oe_pico.value = 0

        tt.reset_project(False)
        time.sleep(0.001)
        tt.clk.off()
        
        self.tt = tt
        
        self.tx_dma = rp2.DMA()
        self.dma_ctrl = self.tx_dma.pack_ctrl(size=0, inc_write=False, treq_sel=0)

        self.read_sm = rp2.StateMachine(1, pio_read_addr, in_base=Pin(27))    

    def read_addr(self):
        self.read_sm.restart()
        self.read_sm.active(1)
        if run_cycles(12, 0) != 0:
            return -1

        val = self.read_sm.get()
        self.read_sm.active(0)

        return val

    def write_data(self, addr):
        # Dummy cycles
        if run_cycles(10, 8) != 0:
            return 0
        
        #tt.uio_oe_pico.value = 0b00110110
        sm = rp2.StateMachine(0, pio_write_data, out_base=Pin(22))
        sm.active(1)
        bytes_written = 0
        
        self.tx_dma.config(read=memoryview(self.program)[addr:],
                      write=sm,
                      ctrl=self.dma_ctrl,
                      count=len(self.program)-addr,
                      trigger=True)

        try:
            bytes_written = clock_out_data()
        finally:
            sm.active(0)
            self.tx_dma.active(0)
            del sm
            Pin(22, Pin.IN)
            Pin(23, Pin.IN)
            Pin(25, Pin.IN)
            Pin(26, Pin.IN)
            
        return bytes_written

    def run_qspi_simple(self, params, program, response):
        self.program = program
        
        loops = 0
        bytes_written = 0
        response.result[9] = 1
        while params.keep_running:
            while self.tt.uio_out[FLASH_CS] == 1 and self.tt.uio_out[RAM_CS] == 1:
                toggle_clock()
            addr = self.read_addr()
            #print(f"Address: {addr}")
            bytes_written += self.write_data(addr & 0xFFFF)
            #print(f"Bytes written: {bytes_written}")
            response.result[0] = self.tt.uo_out.value
            response.result[1:5] = bytes_written.to_bytes(4, 'little')
            loops += 1
            #print(response.result[0])
            response.result[5:9] = loops.to_bytes(4, 'little')
            
            if self.tt.uo_out.value == 255:
                response.result[9] = 3
                return

        response.result[9] = 2

    def run_qspi_in_out(self, params, program, response):
        self.program = program
        tt = self.tt
        
        loops = 0
        data = params.argument_bytes[1:]
        out_idx = 0
        response.result[9] = 1
        in_idx = 0
        tt.ui_in.value = (data[in_idx] & 0x7f)
        in7 = 0
        while params.keep_running:
            while tt.uio_out[FLASH_CS] == 1 and tt.uio_out[RAM_CS] == 1:
                toggle_clock()
            addr = self.read_addr()
            #print(f"Address: {addr}")
            bytes_written = self.write_data(addr & 0xFFFF)
            #print(f"Bytes written: {bytes_written}")
            #print(f"Received: {response.result[out_idx]}")
            
            loops += 1
            #print(response.result[0])
            response.result[5:6] = addr.to_bytes(1, 'little')
            response.result[6:9] = loops.to_bytes(3, 'little')
            
            response.result[out_idx] = tt.uo_out.value
            if self.tt.uo_out.value == 255:
                response.result[9] = 3
                return

            out_idx = (out_idx + 1) % 5
            if in7 == 0:
                tt.ui_in.value = (data[in_idx] & 0x7f) | 0x80
                in7 = 1
                #print(f"Sent: {data[in_idx] & 0x7f:02x}")
            else:
                if in_idx + 1 < len(data): in_idx += 1
                tt.ui_in.value = (data[in_idx] & 0x7f)
                in7 = 0
        response.result[9] = 2
    
def test_count(params:ExperimentParameters, response:ExpResult):
    # Simple program that loops incrementing the outputs
    program = bytes([0x13, 0x04, 0xf0, 0x0f, 0x22, 0xe6, 0x93, 0x04, 0x00, 0x00, 0x26, 0xe0, 0x85, 0x04, 0xf5, 0xbf, 0, 0, 0, 0])

    # Response looks like BYTES_RECEIVED DATA[0..8]
    response.result = bytearray(10)
    
    # get the TT DemoBoard object from params passed in
    tt = params.tt 
    
    # Start up TQV
    tqv = TinyQV(tt)
    tqv.run_qspi_simple(params, program, response)

def test_in_out(params:ExperimentParameters, response:ExpResult):
    # Simple program that reads some data from the inputs and then writes it to the outputs
    # This effectively reverses the 4 bytes of input data to the result
    program = bytes([0x13, 0x04, 0xf0, 0x0f, 0x22, 0xe6, 0x01, 0x45, 0x91, 0x45, 0x12, 0x64, 0x93, 0x74, 0x04, 0x08
                , 0xed, 0xdc, 0x13, 0x74, 0xf4, 0x07, 0x1e, 0x05, 0x41, 0x8d, 0x12, 0x64, 0x93, 0x74, 0x04, 0x08
                , 0xed, 0xfc, 0xfd, 0x15, 0xfd, 0xf1, 0x91, 0x45, 0x93, 0x74, 0xf5, 0x07, 0x26, 0xe0, 0x1d, 0x81
                , 0xfd, 0x15, 0xfd, 0xf9, 0x09, 0xa0, 0x13, 0x04, 0xf0, 0x0f, 0x22, 0xe0, 0xed, 0xbf
                , 0, 0, 0, 0])

    # Response looks like BYTES_RECEIVED DATA[0..8]
    response.result = bytearray(10)
    
    # get the TT DemoBoard object from params passed in
    tt = params.tt 
    
    # Start up TQV
    tqv = TinyQV(tt)
    tqv.run_qspi_in_out(params, program, response)

def test_prime(params:ExperimentParameters, response:ExpResult):
    # Tests whether the input number, provided in 7-bits per byte big endian format, is prime.
    # Outputs 1, 1, 1, 1 if prime, otherwise the smallest factor.
    program = bytes([0x13, 0x04, 0xf0, 0x0f, 0x22, 0xe6, 0x01, 0x45, 0x91, 0x45, 0x12, 0x64, 0x93, 0x74, 0x04, 0x08
, 0xed, 0xdc, 0x13, 0x74, 0xf4, 0x07, 0x1e, 0x05, 0x41, 0x8d, 0x12, 0x64, 0x93, 0x74, 0x04, 0x08
, 0xed, 0xfc, 0xfd, 0x15, 0xfd, 0xf1, 0x25, 0x20, 0x91, 0x45, 0x93, 0x74, 0xf5, 0x07, 0x26, 0xe0
, 0x1d, 0x81, 0xfd, 0x15, 0xfd, 0xf9, 0x09, 0xa0, 0x13, 0x04, 0xf0, 0x0f, 0x22, 0xe0, 0xed, 0xbf
, 0x36, 0x85, 0x82, 0x80, 0x37, 0x45, 0x20, 0x00, 0x13, 0x05, 0x15, 0x08, 0x82, 0x80, 0x89, 0x46
, 0xe3, 0x0a, 0xd5, 0xfe, 0x93, 0x75, 0x15, 0x00, 0xe5, 0xd5, 0x85, 0x46, 0x89, 0x06, 0xe3, 0x83
, 0xa6, 0xfe, 0xb3, 0x85, 0xd6, 0x04, 0xe3, 0x8d, 0xa5, 0xfc, 0xe3, 0x4d, 0xb5, 0xfc, 0x36, 0x86
, 0x36, 0x96, 0xe3, 0x07, 0xa6, 0xfc, 0xe3, 0x4d, 0xa6, 0xfe, 0xcd, 0xb7
                    , 0, 0, 0, 0])

    # Response looks like BYTES_RECEIVED DATA[0..8]
    response.result = bytearray(10)
    
    # get the TT DemoBoard object from params passed in
    tt = params.tt
    
    # Start up TQV
    tqv = TinyQV(tt)
    tqv.run_qspi_in_out(params, program, response)
