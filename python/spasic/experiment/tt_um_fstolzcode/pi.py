'''
Created on May 3, 2025

@author: Florian Stolz
@copyright: Copyright (C) 2025 Florian Stolz, https://informatik.rub.de/seceng/personen/stolz/
'''

import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

from machine import UART, Pin

def setR1(ser, x):
    time.sleep(0.5)
    ser.write(b'\x82')
    time.sleep(0.5)
    ser.write(x)

def setR2(ser, x):
    time.sleep(0.5)
    ser.write(b'\x83')
    time.sleep(0.5)
    ser.write(x)

def readFromSer(ser, numbytes):
    # was occasionally getting None from read()
    # this ensures we have as many bytes as 
    # expected, in a form with 'buffer protocol' support
    result = ser.read(numbytes)
    if result is None:
        return bytearray([0xff]*numbytes)
    
    if len(result) == numbytes:
        return result 
    
    bts = bytearray(result)
    if len(bts) < numbytes:
        bts.extend([0]*(numbytes - len(bts)))
        
    return bts

def readRes(ser):
    time.sleep(0.5)
    ser.write(b'\x87')
    result = readFromSer(ser, 3)
    
    return result

def readR1(ser):
    time.sleep(0.5)
    ser.write(b'\x85')
    result = readFromSer(ser, 3)
    return result

def readR2(ser):
    time.sleep(0.5)
    ser.write(b'\x86')
    result = readFromSer(ser, 3)
    return result

def moveResToR1(ser):
    result = readRes(ser)
    setR1(ser, result)
    return result

def moveResToR2(ser):
    result = readRes(ser)
    setR2(ser, result)
    return result

def add(ser):
    time.sleep(0.5)
    ser.write(b'\x88')


def sub(ser):
    time.sleep(0.5)
    ser.write(b'\x89')

def mul(ser):
    time.sleep(0.5)
    ser.write(b'\x8a')

def div(ser):
    time.sleep(0.5)
    ser.write(b'\x8b')

def sqrt(ser):
    time.sleep(0.5)
    ser.write(b'\x8c')

def test_pi(params:ExperimentParameters, response:ExpResult, num_iterations:int=50):    
    status_string = bytearray(5)
    fpu_result = bytearray(3)

    response.result = status_string + fpu_result
    
    # get the TT DemoBoard object from params passed in
    tt = params.tt 

    # Use the TT object to load tinyZuse
    tt.shuttle.tt_um_fstolzcode.enable()

    # Setup clock to 10 MHz
    tt.clock_project_PWM(10e6)

    # Keep in reset
    tt.reset_project(True)

    # Setup UART
    ser = UART(0, baudrate=9600, tx=Pin(12), rx=Pin(13),timeout=2)

    # Go out of reset
    tt.reset_project(False)

    # Get any garbage out of the UART buffer
    garbage = ser.read(128)

    # Preliminary Tests to check if basic functions are working
    # 42.75 + 7.0 = 49.75
    setR1(ser, b'\x85\xab\x00')
    if readR1(ser) != b'\x85\xab\x00':
        status_string[0] = 0x1

    response.result = status_string + fpu_result

    setR2(ser, b'\x82\xe0\x00')
    if readR2(ser) != b'\x82\xe0\x00':
        status_string[0] = 0x2

    response.result = status_string + fpu_result

    add(ser)
    if readRes(ser) != b'\x85\xc7\x00':
        status_string[0] = 0x3

    response.result = status_string + fpu_result

    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 
    # Pi Approximation via ( sqrt(58)/4 - 37sqrt(2)/33)^-1
    # See: https://en.wikipedia.org/wiki/Approximations_of_π
    # Mathematics by Experiment: Plausible Reasoning in the 21st Century, 2nd Edition. A.K. Peters. p. 135
    
    # Set R1 = 58
    setR1(ser, b'\x85\xe8\x00')

    sqrt(ser)

    temp = moveResToR1(ser) 
    if temp ==  b'\xff\xff\xff':
        status_string[1] = 0x1
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(temp)
    status_string[2] = 0x1
    response.result = status_string + fpu_result
    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 

    # Set R2 = 4
    setR2(ser, b'\x82\x80\x00')

    div(ser)

    intermediate_1 = readRes(ser)
    if intermediate_1 ==  b'\xff\xff\xff':
        status_string[1] = 0x2
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(intermediate_1)
    status_string[2] = 0x2
    response.result = status_string + fpu_result
    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 

    # Set R1 = 2
    setR1(ser, b'\x81\x80\x00')

    sqrt(ser)
    
    temp = moveResToR1(ser)
    if temp == b'\xff\xff\xff':
        status_string[1] = 0x3
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(temp)
    status_string[2] = 0x3
    response.result = status_string + fpu_result
    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 

    # Set R2 = 37
    setR2(ser, b'\x85\x94\x00')

    mul(ser)

    temp = moveResToR1(ser)
    if temp == b'\xff\xff\xff':
        status_string[1] = 0x4
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(temp)
    status_string[2] = 0x4
    response.result = status_string + fpu_result
    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 

    # Set R2 = 33
    setR2(ser, b'\x85\x84\x00')

    div(ser)

    temp = moveResToR2(ser)
    if temp == b'\xff\xff\xff':
        status_string[1] = 0x5
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(temp)
    status_string[2] = 0x5
    response.result = status_string + fpu_result
    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 

    # Set R1 = intermediate_1 
    setR1(ser, intermediate_1)

    sub(ser)

    temp = moveResToR2(ser)
    if temp == b'\xff\xff\xff':
        status_string[1] = 0x6
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(temp)
    status_string[2] = 0x6
    response.result = status_string + fpu_result
    if not params.keep_running:
        # have been asked to terminate, make note and return
        status_string[3] = 0x1
        response.result = status_string + fpu_result
        return 

    # Set R1 = 1
    setR1(ser, b'\x80\x80\x00')

    div(ser)

    pi_approx = readRes(ser)

    if pi_approx == b'\xff\xff\xff':
        status_string[1] = 0x7
        fpu_result = bytearray(3)
    else:
        fpu_result = bytearray(pi_approx)
    status_string[2] = 0x7
    response.result = status_string + fpu_result

    # Expected Result: 3.140869140625 (b'\x81\xc9\x04') (numerical errors add up)
    # Expected Output: bytearray(b'\x00\x00\x07\x00\x00\x81\xc9\x04'

    return
 