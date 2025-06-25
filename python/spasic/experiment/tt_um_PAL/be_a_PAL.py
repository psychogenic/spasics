# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Ken Pettit

from spasic.experiment.experiment_parameters import ExperimentParameters
from spasic.experiment.experiment_result import ExpResult
from ttboard.cocotb.dut import DUT
from ttboard.demoboard import DemoBoard
from machine import Pin, UART

class PALController(DUT):
    def __init__(self, tt: DemoBoard):
        super().__init__("DUT")
        self.tt = tt
        tt.uio_oe_pico.value = 0b00000111 
        self.i_clk    = self.new_bit_attribute("i_clk", tt.uio_in, 2)
        self.i_config = self.new_bit_attribute("i_config", tt.uio_in, 0)
        self.i_enable = self.new_bit_attribute("i_enable", tt.uio_in, 1)

        self.i_ascii  = self.new_slice_attribute("i_ascii", tt.ui_in, 4, 0)
        self.i_state  = self.new_slice_attribute("i_state", tt.ui_in, 7, 5)

        self.o_state  = self.new_slice_attribute("o_state", tt.uo_out, 2, 0)
        self.o_valid  = self.new_bit_attribute("o_valid", tt.uo_out, 3)
        self.o_done   = self.new_bit_attribute("o_done", tt.uo_out, 4)
        self.o_all    = self.new_slice_attribute("o_all", tt.uo_out, 4, 0)

    def prog(self, data, num_bits, params, response):
        n = len(data)
        bits = 0
        self.i_enable.value = 0
        self.i_clk.value    = 0

        # Loop for all bytes
        for i in range(n):
            d = data[n-i-1]
            response.result[0] = i
            response.result[1] = d
            for b in range(8):
                if not params.keep_running:
                    return

                # Set next config bit
                self.i_config.value = d & 0x01
                self.i_clk.value    = 1
                self.i_clk.value    = 0

                # Shift the data
                d = d >> 1

                # Increment bit count
                bits += 1
                if bits >= num_bits:
                    break

            if bits >= num_bits:
                break

        # Now enable the config
        self.i_enable.value = 1

# ======================================================
# This is the main test entry
# ======================================================
def exercise(params: ExperimentParameters, response: ExpResult):
    # Result is up to 10 bytes
    response.result = bytearray(10)
    
    # Enable PAL
    tt = params.tt
    tt.shuttle.tt_um_MATTHIAS_M_PAL_TOP_WRAPPER.enable()
    tt.reset_project(True)
    tt.reset_project(False)
    
    # Create a PAL controller
    pal = PALController(tt)
    
    PROG1 = [0x5F, 0x14, 0x1C, 0x34, 0x79, 0x73, 0xA5, 0x8B,
             0x6A, 0x12, 0xBD, 0x04, 0x3F, 0x78, 0x0F, 0xFE,
             0x03, 0x47, 0x97, 0x03, 0x2F, 0x9A, 0xFC, 0x06,
             0xF0, 0x33, 0x7F, 0xF1, 0x00]
    PROG2 = [0x13, 0x7D, 0x91, 0xC9, 0x46, 0xDE, 0xA4, 0x2B,
             0x58, 0xD4, 0xE5, 0x0C, 0x5E, 0x74, 0x0F, 0xFE,
             0x03, 0x47, 0x97, 0x03, 0x2F, 0x9A, 0xFC, 0x06,
             0xF0, 0x33, 0x7F, 0xF1, 0x00]
    
    # Prepare to send a string message to the PAL
    if params.argument_bytes[0] == 1:
        pal.prog(PROG2, 232, params, response)
        msg = "DON'T PANIC" 
    else:
        pal.prog(PROG1, 232, params, response)
        msg = "HELLO SPACE" 
    
    if not params.keep_running:
        return
    
    # Initial condition
    state = 0
    done = 0
    pal.i_state.value = state
    
    # Loop for all characters
    for char in msg:
        if not params.keep_running:
            return
        
        if char == ' ':
            v = 0
        elif char == "'":
            v = 0x1f
        else:
            v = ord(char) - ord('A') + 1
        
        # Set the next ASCII value
        pal.i_ascii.value = v
        
        # Test for valid response
        if pal.o_valid.value == 1:
            print(f'Detected {char}')
            
            # Get the next state
            state = int(pal.o_state.value)
            
            # Test if 'done' detected
            if int(pal.o_done.value) == 1:
                done = 1
            
            # assign the new state
            pal.i_state.value = state
        
        else:
            response.result[0] = ord('F')
            response.result[1] = ord('A')
            response.result[2] = ord('I')
            response.result[3] = ord('L')
            response.result[4] = 0
            response.result[5] = state
            response.result[6] = ord(char)
            response.result[7] = int(pal.o_all.value)
            
            print(f'State: {state}  Failed to detect {char}')
            break
    
    # Test if the FSM cycled through detection of the string
    if done:
        print(f'Done detected')
        if msg == "HELLO SPACE":
            response.result[0] = ord('W')
            response.result[1] = ord('h')
            response.result[2] = ord('y')
            response.result[3] = ord(' ')
            response.result[4] = ord('H')
            response.result[5] = ord('e')
            response.result[6] = ord('l')
            response.result[7] = ord('l')
            response.result[8] = ord('o')
            response.result[9] = 0
        else:
            response.result[0] = ord('4')
            response.result[1] = ord('2')
            response.result[2] = 0
    
    print(response.result)

# vim: sw=2 ts=2 et

