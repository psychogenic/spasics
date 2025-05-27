'''
Created on Apr 30, 2025

@author: Andrewtron3000
@copyright: Copyright (C) 2025 Andrewtron3000 (https://github.com/andrewtron3000)
'''

import time
import struct

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

from machine import UART, Pin
from ttboard.mode import RPMode

BUF_SIZE_BYTES = 32

def set_error_response(response:ExpResult):
    error_response = b'Stratos is in Space!'
    response.result[0:len(error_response)] = error_response
    return response

def run_test(params:ExperimentParameters, response:ExpResult, num_iterations:int=50):

    # we'll send a simple response result, bytes from the UART
    response.result = bytearray(BUF_SIZE_BYTES)

    clock, baud, uart_timeout = struct.unpack('<IIH', params.argument_bytes)
    if clock == 0:
        clock = 50_000_000
    if baud == 0:
        baud = 115_200
    if uart_timeout == 0:
        uart_timeout = 40

    # get the TT DemoBoard object from params passed in
    tt = params.tt 

    # Create the UART
    uart = UART(0, 
                baudrate=baud, 
                timeout=uart_timeout, 
                timeout_char=uart_timeout, 
                rxbuf=BUF_SIZE_BYTES, 
                rx=tt.pins.uo_out4.raw_pin, 
                tx=tt.pins.ui_in3.raw_pin)

    # Stop any clocking
    tt.clock_project_stop()

    # Start the design
    tt.shuttle.tt_um_andrewtron3000.enable()

    # Configure uio pins to inputs
    tt.mode = RPMode.ASIC_RP_CONTROL
    tt.uio_oe_pico.value = 0b11111111

    # Define starting values for the ui and uio.
    # 0xa5 in the uio_in is the secret message mode.
    tt.ui_in.value = 0x80
    tt.uio_in.value = 0xa5

    # Run the test for the given number of iterations.
    for it in range(num_iterations):
        if not params.keep_running:
            # have been asked to terminate
            response = set_error_response(response)
            return

        # Stop all clocking
        tt.clock_project_stop()

        # reset project
        tt.reset_project(True)

        tt.clock_project_once() # tick
        tt.clock_project_once() # tick
        tt.clock_project_once() # tick
        tt.clock_project_once() # tick

        # Empty anything in the UART
        while(uart.any() > 0):
            if not params.keep_running:
                # have been asked to terminate
                response = set_error_response(response)
                return 
            # Perform a read to empty UART data
            uart.read(BUF_SIZE_BYTES)

        # Start clocking the design
        tt.clock_project_PWM(clock)

        # release from reset
        tt.reset_project(False)

        # Read data from the UART.
        uart_data = uart.read(BUF_SIZE_BYTES)

        # If we see what we're expecting, end immediately, test successful!
        if uart_data:
            # Put the uart_data into the response.
            response.result = bytearray(uart_data)
            # The UART data should include the word "Stratos".  If it does,
            # this means the UART data collection was successful and this
            # test is successful.  We can return the collected data as the
            # test response.
            if b"Stratos" in response.result:
                return

    # If we have fallen through the test loop, set the error response
    # and return.
    response = set_error_response(response)
    return
