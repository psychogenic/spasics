'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
import micropython
import machine
import _thread
from ttboard.demoboard import DemoBoard # keep this
import i2c_server_globals as i2cglb
import spasic.cnc.response.response as rsp
import spasic.settings as sts

if sts.DebugUseSimulatedI2CDevice:
    from spasic.i2c.device_sim import I2CDevice
else:
    from spasic.i2c.device import I2CDevice
    
import spasic.error_codes as error_codes
from spasic.experiment.experiment_list import ExperimentsAvailable
from ttboard.mode import RPMode
import spasic.util.watchdog

import i2c_server_handlers as handlers
from i2c_server_handlers import queue_response



def tx_done_cb():
    pass # print('i2c tx done')
    
def tx_buffer_empty_cb():
    pass # print('i2c buffer empty')




def i2c_data_in(numbytes:int, bts:bytearray):
    btslen = int(numbytes)
    if btslen > 8:
        btslen = 8
        
    if len(bts) and btslen:
        i2cglb.PendingDataIn[i2cglb.PendingDataNum][0] = btslen
        for i in range(btslen):
            i2cglb.PendingDataIn[i2cglb.PendingDataNum][i+1] = bts[i]
        i2cglb.PendingDataNum += 1


    
def out_queue_length():
    return len(i2cglb.PendingDataOut)
    
def get_and_flush_pending_in():
    if not i2cglb.PendingDataNum:
        return []
    
    # race condition ?
    data_rcvd_with_len = list(i2cglb.PendingDataIn)
    num_msg = int(i2cglb.PendingDataNum)
    i2cglb.PendingDataNum = 0
    
    data_rcvd = []
    for i in range(num_msg):
        bts = data_rcvd_with_len[i]
        data_rcvd.append(bts[1:bts[0]+1])
    return data_rcvd 

def process_pending_data():
    data_rcvd = get_and_flush_pending_in()
    if not len(data_rcvd):
        return 0

    # any handler that's involved is found in 
    # i2c_server_handlers.  Small ones, and the 
    # experiment runner, are directly here
    for bts in data_rcvd:
        typebyte = bts[0]
        payload = bts[1:]
        if typebyte == ord('A'):
            print("Abort")
            i2cglb.ExpArgs.clear_swap()
            handlers.abort()
                
        elif typebyte == ord('E'):
            print("Run")
                
            if i2cglb.ERes.running:
                # cancel all args in swap
                i2cglb.ExpArgs.clear_swap()
                queue_response(rsp.ResponseError(error_codes.Busy, 
                                                      i2cglb.ERes.expid.to_bytes(2, 'little')))
                return 
            
            exp_argument_bytes = None
            if len(payload):
                exp_id = int.from_bytes(payload[:2], 'little')
                if len(payload) > 2:
                    exp_argument_bytes = payload[2:]
                    i2cglb.ExpArgs.argument_swap += exp_argument_bytes
            else:
                exp_id = 0
                
            if exp_id not in ExperimentsAvailable:
                i2cglb.ExpArgs.clear_swap()
                queue_response(rsp.ResponseError(error_codes.UnknownExperiment, bytearray([exp_id])))
                return 
            arglen = len(i2cglb.ExpArgs.argument_swap)
            if  arglen < 14:
                i2cglb.ExpArgs.argument_swap += bytearray(14 - arglen)
                
            
            i2cglb.ERes.expid = exp_id
            i2cglb.ERes.start()
            i2cglb.ExpArgs.start(i2cglb.ExpArgs.argument_swap)
            
            # print(f"exp args for run {i2cglb.ExpArgs.argument_bytes}")
            
            # clear swap
            i2cglb.ExpArgs.clear_swap()
            i2cglb.ExperimentRun = True
            
            respmsg = b'EXP'
            respmsg += exp_id.to_bytes(2, 'little')
            
            # ok response
            responseObj = rsp.ResponseOKMessage(respmsg)
            
            # always ensure we start fresh in ASIC_RP_CONTROL mode,
            # just in case an experiment messed with it.
            DemoBoard.get().mode = RPMode.ASIC_RP_CONTROL
            
            runner = ExperimentsAvailable[exp_id]
            try:
                _thread.start_new_thread(runner, (i2cglb.ExpArgs, i2cglb.ERes,))
            except:
                # the only reason this might throw, afaik, is 
                # if something is already running on core1...
                # either way: not working out, return error instead
                responseObj = rsp.ResponseError(error_codes.UnterminatedCore1Experiment, b'CORBZY')
                
            queue_response(responseObj)
        elif typebyte == ord('E') + ord('A'):
            # experiment args
            print("ExpArg")
            if not len(i2cglb.ExpArgs.argument_swap):
                i2cglb.ExpArgs.argument_swap = payload 
            else:
                i2cglb.ExpArgs.argument_swap += payload 
                
            # print(f"Parms now {i2cglb.ExpArgs.argument_swap}")
            
        elif typebyte == ord('E') + ord('Q'):
            # experiment queue
            if len(payload):
                exp_id = int.from_bytes(payload[:2], 'little')
                if len(payload) > 2:
                    exp_argument_bytes = payload[2:]
                    i2cglb.ExpArgs.argument_swap += exp_argument_bytes
            else:
                exp_id = 0
                
            if exp_id not in ExperimentsAvailable:
                i2cglb.ExpArgs.clear_swap()
                queue_response(rsp.ResponseError(error_codes.UnknownExperiment, bytearray([exp_id])))
                return 
            
            i2cglb.ExperimentQueue.append((exp_id, i2cglb.ExpArgs.argument_swap,))
            i2cglb.ExpArgs.clear_swap()
            queue_response(rsp.ResponseOKMessage(bytearray([ord('E'), ord('Q'), exp_id % 256])))
            
                
        elif typebyte == ord('E') + ord('I'):
            # experiment immediate result
            print("ExpImm")
            res = i2cglb.ERes
            if not res.expid:
                queue_response(rsp.ResponseError(error_codes.UnknownExperiment, b'NOXP'))
                return 
            
            queue_response(rsp.ResponseExperiment(res.expid, res.completed, 
                                                  res.exception_type_id, 
                                                  res.result))
            
        elif typebyte == ord('F'):
            # b'FS' VARID -- read size
            # b'FZ' VARID -- read checksum
            # b'FO' VARID 'R'|'W' -- open for read or write
            # b'FD' VARID -- make a directory (including parents)
            # b'FU' VARID -- unlink/delete a file
            # b'FM' SRCVARID DESTVARID -- move SRC to DEST
            return handlers.fs_action_on_vid(payload)
        
        elif typebyte == ord('F') + ord('C'):
            print("file close")
            handlers.fs_file_close()
                
        elif typebyte == ord('F') + ord('R'):
            handlers.fs_file_read(payload)
            
        elif typebyte == ord('F') + ord('W'):
            handlers.fs_file_write(payload)
        elif typebyte == ord('I'):
            handlers.info()
        elif typebyte == ord('P'):
            print("Ping")
            queue_response(rsp.ResponseOKMessage(payload))
        elif typebyte == ord('R'):
            print("Reboot")
            spasic.util.watchdog.force_reboot()
            queue_response(rsp.ResponseOK())

        elif typebyte == ord('S'):
            print("Status")
            res = i2cglb.ERes
            queue_response(rsp.ResponseStatus(res.running, res.expid, res.exception_type_id,
                                              res.run_duration, res.result))
            
        elif typebyte == ord('T'):
            print("Clock")
            handlers.time_sync(payload)
        elif typebyte == ord('V'):
            print("Var get")
            handlers.variable_get(payload)
        
        elif typebyte == ord('V') + ord('S'):
            print("Var set")
            handlers.variable_set(payload)
            
        elif typebyte == ord('V') + ord('A'):
            print("Var app")
            handlers.variable_append(payload)

_I2CDevSingleton = None
def get_i2c_device():
    global _I2CDevSingleton
    if _I2CDevSingleton is None:
        # create our slave device
        _I2CDevSingleton = I2CDevice(address=sts.DeviceAddress, scl=sts.I2CSCL, sda=sts.I2CSDA,
                        baudrate=sts.I2CBaudRate)
    
    return _I2CDevSingleton


def POST(numiterations:int=2):
    print("\n\nPerforming POST!\n")
    arg_bytes = bytearray([numiterations, 0, 0])
    status = debug_launch_experiment(1, arg_bytes)
    if not status:
        print("Problem launching")
        return
    else:
        print("Running")
        while status.running:
            time.sleep(0.5)
            print(status.result)
            
        num_fails = int.from_bytes(status.result[0:4], 'little')
        if num_fails:
            print(f"Had {num_fails} failures on first test, skipping second.")
            ret_bytes = bytearray(5)
            ret_bytes[0:4] = num_fails.to_bytes(4, 'little')
            queue_response(rsp.ResponseError(error_codes.POSTTestFail, ret_bytes))
            return
        
        print("Done!  Launching bidirs")
        arg_bytes[2] = 1
        status = debug_launch_experiment(1, arg_bytes)
        while status.running:
            time.sleep(0.5)
            print(status.result)
            
        num_fails += int.from_bytes(status.result[0:4], 'little')
        
        if num_fails:
            ret_bytes = bytearray(5)
            ret_bytes[4] = 1
            ret_bytes[0:4] = num_fails.to_bytes(4, 'little')
            queue_response(rsp.ResponseError(error_codes.POSTTestFail, ret_bytes))
        else:
            queue_response(rsp.ResponseOKMessage(b'POST'))
            
        if num_fails:
            print(f"\nPOST FAILURES: {num_fails}\n")
        else:
            print(f"\nTotal failures: 0\n POST OK!")
        
def begin():
    micropython.mem_info()
    i2c_dev = get_i2c_device()
    # setup the callbacks
    i2c_dev.callback_data_in = i2c_data_in
    i2c_dev.callback_tx_done = tx_done_cb 
    i2c_dev.callback_tx_buffer_empty = tx_buffer_empty_cb
    
    # init the i2c device and start listening
    print("i2c:")
    if i2c_dev.begin():
        print("  success")
        return True
    print("  init?")
    return False
def experiment_terminate():
    if not i2cglb.ERes.running:
        print("Nothing running")
        return 
    
    i2cglb.ExpArgs.terminate()
    
    print("Termination requested")
    
def debug_launch_experiment(exp_id:int, exp_argument_bytes:bytearray=None):
    print("Test Exp")
    if i2cglb.ERes.running:
        print("Already busy!")
        return False
        
    if exp_id not in ExperimentsAvailable:
        print("Unknown exp")
        return False
    
    if exp_argument_bytes is None:
        exp_argument_bytes = bytearray(10)
    
    i2cglb.ERes.expid = exp_id
    i2cglb.ERes.start()
    i2cglb.ExpArgs.start(exp_argument_bytes)
    
    # always ensure we start fresh in ASIC_RP_CONTROL mode,
    # just in case an experiment messed with it.
    DemoBoard.get().mode = RPMode.ASIC_RP_CONTROL
    
    runner = ExperimentsAvailable[exp_id]
    try:
        _thread.start_new_thread(runner, (i2cglb.ExpArgs, i2cglb.ERes,))
    except:
        # the only reason this might throw, afaik, is 
        # if something is already running on core1...
        # either way: not working out, return error instead
        print("Core BZY!")
        return False
    
    print("Launched")
        
    return i2cglb.ERes

def process_experiment_queue():
    if not len(i2cglb.ExperimentQueue):
        return 
    print('procQ')
    exp_data = i2cglb.ExperimentQueue[0]
    print(f"EXP DATA: {exp_data}")
    i2cglb.ExperimentQueue = i2cglb.ExperimentQueue[1:]
    if len(exp_data[1]):
        i2cglb.ExpArgs.argument_swap = exp_data[1]
    else:
        i2cglb.ExpArgs.argument_swap = bytearray()
    fakemsg = bytearray([ord('E')])
    fakemsg += exp_data[0].to_bytes(2, 'little')
    i2c_data_in(3, fakemsg)
    
def main_loop(runtimes:int=0):
    i2c_dev = get_i2c_device()
    loop_count = 0
    while True and (runtimes == 0 or loop_count < runtimes):
        loop_count += 1
        try:
            # check if low-level i2c has 
            # flagged pending data and, if so, 
            # trigger the fetch/user-callback mech 
            # to move this data into our globals here
            i2c_dev.poll_pending_data()
            
            # if an experiment run is ongoing
            # but it's no longer stating itself 
            # as running, then it has completed: queue 
            # the experiment response for output
            if i2cglb.ExperimentRun:
                res = i2cglb.ERes
                if not res.running:
                    # experiment is done!
                    i2cglb.ExperimentRun = False 
                    print("exp done, queue result")
                    queue_response(rsp.ResponseExperiment(res.expid, res.completed, 
                                                          res.exception_type_id, 
                                                          res.result))
                    
                    process_experiment_queue()
            else:
                process_experiment_queue()
            
            
            # if the poll_pending_data() queued up some 
            # some pending incoming bytes, pass all of 
            # those through the processor function, which
            # will likely produce some output to send back
            # as responses
            num_incoming = process_pending_data()
            if num_incoming:
                print(f"{num_incoming} msgs")
                
            # pending output data may be split into
            # little chunks of less that 16 bytes, which is
            # how much gets read out at a time.  We smoosh 
            # all this into one contiguous bytearray
            out_data = bytearray()
            for outbytes in i2cglb.PendingDataOut:
                out_data += outbytes
            
            # reset the global out data list
            i2cglb.PendingDataOut = []
            
            # if we have some out data, shoot that 
            # off to the device so it can feed it 
            # out to master as it requests it
            if len(out_data):
                print(f"data out: {out_data}")
                i2c_dev.queue_outdata(out_data)
                
            i2c_dev.push_outgoing_data()
            
            # sleep a bit to yield so under the hood
            # magiks can happen if required
            time.sleep_ms(1)
                
        except Exception as e:
            print(f'ml ex: {e}')
            # report this unexpected error
            # but don't send a storm of them, if something 
            # goes terribly wrong
            if (out_queue_length() < 6 and i2c_dev.outdata_queue_size < (16*5)):
                except_id = i2cglb.ExpResult.exception_to_id(e)
                
                ex_type_bts = bytearray([except_id])
                
                if e.value is not None:
                    try:
                        if len(e.value):
                            ex_type_bts += bytearray(e.value, 'ascii')
                        if len(ex_type_bts) > 12:
                            ex_type_bts = ex_type_bts[:12]
                    except:
                        pass
                
                print(f"EX {except_id}: {ex_type_bts}")
                queue_response(rsp.ResponseError(error_codes.RuntimeExceptionCaught, ex_type_bts))
                if sts.DebugUseSimulatedI2CDevice or sts.RaiseAndBreakMainOnException:
                    raise e
