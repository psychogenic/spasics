'''
Created on Jun 15, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com


An experiment for the nicely documented https://tinytapeout.com/runs/tt06/tt_um_CKPope_top
by Charles Pope, a Two-Axis position Controller (4 bits of range per axis).


'''
import random
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

DoOutputDebug = False

def get_current_position(tt):
    # get current position, stored in uo_out
    # as 4-bit chunks
    # x: low nibble
    current_x = int(tt.uo_out[3:0])
    # y: high nibble
    current_y = int(tt.uo_out[7:4])
    
    return (current_x, current_y)

def set_random_target(tt):
    # get current x/y, stored in ui_in
    current_target_y = int(tt.ui_in[3:0])
    current_target_x = int(tt.ui_in[7:4])
    
    # select random x/y
    xpos = random.randint(0, 15)
    ypos = random.randint(0, 15)
    
    # ensure we move some amount, and we don't aim for 0,0
    while xpos == current_target_x and ypos == current_target_y or (xpos == 0 and ypos == 0):
        xpos = random.randint(0, 15)
        ypos = random.randint(0, 15)
    
    # set the target position
    tt.ui_in = xpos | (ypos << 4) 
    
    output_debug(f'Sending to {xpos},{ypos}')
    
    return (xpos, ypos)

def trigger_motion(params):
    
    tt = params.tt
    # bring motion_inp (bidir bit 0) high
    tt.uio_in[0] = 1
    
    # give a bit of time for things to latch
    # giving 20 "single" clock pulses
    tt.clock_project_once(200)
    
    tt.uio_in[0] = 0
    
    tt.clock_project_once(100)
    
    (start_x, start_y) = get_current_position(tt)
    
    
    # this thing takes a while to get off the ground
    # so we just clock a bit and see if we've started to move
    # yet
    num_wait = 0
    while num_wait < 100:
        num_wait += 1
        tt.clock_project_once(100)
        if not params.keep_running:
            output_debug("We've been aborted in trigger_motion")
            return False
        (current_x, current_y) = get_current_position(tt)
        if current_x != start_x or current_y != start_y:
            # we've started moving!
            return True 
        
    return False
    
def setup_project(tt):
    tt.shuttle.tt_um_CKPope_top.enable()
    
    # put the project in reset
    tt.reset_project(True)
    
    # stop any default auto-clocking
    tt.clock_project_stop()
    
    # we want the lower bit of bidir to be an output:
    tt.uio_oe_pico = 1
    
    # motion trip low:
    tt.uio_in[0] = 0
    tt.ui_in = 0 
    
    # take the project out of reset
    tt.reset_project(False)
    tt.clock_project_once(50)
    tt.uio_in[0] = 0
    tt.clock_project_once(500)
            
def test_xy_motion(params:ExperimentParameters, response:ExpResult, num_iterations:int=20):
    
    # we'll send a simple response result, 8 bytes
    # SUCCESS_COUNT FAIL_COUNT NUM_ITERATIONS CURRENT_ITERATION CURRENT_TARGX CURRENT_TARGY CURX CURY
    response.result = bytearray(8)
    
    idx_success = 0
    idx_fails = 1
    idx_num_iter = 2
    idx_current_iter = 3
    idx_current_targ_x = 4
    idx_current_targ_y = 5
    idx_current_x = 6
    idx_current_y = 7
    
    response.result[idx_num_iter] = num_iterations % 255 
    
    
    # select the project
    tt = params.tt
    
    setup_project(tt)
    
    iter_count = 0 
    while iter_count < num_iterations:
        
        iter_count += 1
        # update result with current iteration
        response.result[idx_current_iter] = iter_count
        
        
        (target_x, target_y) = set_random_target(tt)
        
        # update result with current target
        response.result[idx_current_targ_x] = target_x
        response.result[idx_current_targ_y] = target_y
        
        
        # check if abort requested
        if not params.keep_running:
            # aborted 
            return
        
        if not trigger_motion(params):
            # could not trigger motion?
            response.result[idx_fails] += 1
            continue
        
        (last_x, last_y) = get_current_position(tt)
        output_debug(f'Start pos: {last_x},{last_y}')
        delta_x = abs(last_x - target_x)
        delta_y = abs(last_y - target_y)
        while delta_x or delta_y:
            tt.clock_project_once()
            print('.', end='')
            if not params.keep_running:
                # aborted 
                return
            
            (cur_x, cur_y) = get_current_position(tt)
            response.result[idx_current_x] = cur_x 
            response.result[idx_current_y] = cur_y 
            
            
            delta_x = abs(cur_x - target_x)
            delta_y = abs(cur_y - target_y)
            
            if delta_x == 0 and delta_y == 0:
                # note success 
                output_debug(f'\nMade it to {target_x},{target_y}')
                print('!')
                response.result[idx_success] += 1
            else:
                mov_x = abs(cur_x - last_x)
                mov_y = abs(cur_y - last_y)
                if not (mov_x or mov_y):
                    # not there but haven't moved??
                    output_debug(f'Not there but not moving (targ {target_x},{target_y}) pos ({cur_x},{cur_y})')
                    
                last_x = cur_x
                last_y = cur_y
                
def output_debug(msg):
    if DoOutputDebug:
        print(msg)