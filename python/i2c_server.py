'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import time
import gc
import micropython
import machine
import _thread
import spasic.cnc.response.response as rsp
import spasic.settings as sts
from spasic.i2c.device import I2CDevice
import spasic.error_codes as error_codes
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters
from spasic.experiment.experiment_list import ExperimentsAvailable
from ttboard.demoboard import DemoBoard
import spasic.util.watchdog
import random
ERes = ExpResult()
ExpArgs = ExperimentParameters(DemoBoard.get())




def tx_done_cb():
    pass # print('i2c tx done')
    
def tx_buffer_empty_cb():
    pass # print('i2c buffer empty')


PendingDataIn = [bytearray(9), bytearray(9), bytearray(9)]
PendingDataNum = 0

PendingDataOut = []
ExperimentRun = False
LastTimeSyncMessageTime = -1
LastTimeSyncValue = 0

def i2c_data_in(numbytes:int, bts:bytearray):
    global PendingDataIn 
    global PendingDataNum
    btslen = int(numbytes)
    if btslen > 8:
        btslen = 8
        
    if len(bts) and btslen:
        PendingDataIn[PendingDataNum][0] = btslen
        for i in range(btslen):
            PendingDataIn[PendingDataNum][i+1] = bts[i]
        PendingDataNum += 1


def queue_response(response:rsp.Response):
    global PendingDataOut
    PendingDataOut.append(response.bytes)
    
def out_queue_length():
    global PendingDataOut
    return len(PendingDataOut)
    
def get_and_flush_pending_in():
    global PendingDataIn, PendingDataNum
    # machine.disable_irq()
    if not PendingDataNum:
        # machine.enable_irq()
        return []
    
    # race condition ?
    data_rcvd_with_len = list(PendingDataIn)
    num_msg = int(PendingDataNum)
    PendingDataNum = 0
    
    data_rcvd = []
    for i in range(num_msg):
        bts = data_rcvd_with_len[i]
        # print(f'{bts} {bts[0]}')
        data_rcvd.append(bts[1:bts[0]+1])
    #machine.enable_irq()
    return data_rcvd 

def process_pending_data():
    global ExperimentRun
    global LastTimeSyncMessageTime
    global LastTimeSyncValue
    data_rcvd = get_and_flush_pending_in()
    if not len(data_rcvd):
        return 0

    
    for bts in data_rcvd:
        typebyte = bts[0]
        payload = bts[1:]
        if typebyte == ord('A'):
            print("Abort")
            ExpArgs.terminate()
            if ERes.running:
                respmsg = b'TRM'
                respmsg += ERes.expid.to_bytes(2, 'little')
                queue_response(rsp.ResponseOKMessage(respmsg))
            else:
                queue_response(rsp.ResponseOK())
                
        elif typebyte == ord('E'):
            print("Run")
                
            if ERes.running:
                queue_response(rsp.ResponseError(error_codes.Busy, 
                                                      ERes.expid.to_bytes(2, 'little')))
                return 
            
            exp_argument_bytes = None
            if len(payload):
                exp_id = int.from_bytes(payload[:2], 'little')
                if len(payload) > 2:
                    exp_argument_bytes = payload[2:]
                    if len(exp_argument_bytes) < 10:
                        exp_argument_bytes += bytearray(10 - len(exp_argument_bytes))
            else:
                exp_id = 0
                
            if exp_id not in ExperimentsAvailable:
                queue_response(rsp.ResponseError(error_codes.UnknownExperiment, bytearray([exp_id])))
                return 
            
            
            ERes.expid = exp_id
            ERes.start()
            ExpArgs.start(exp_argument_bytes)
            ExperimentRun = True
            
            respmsg = b'EXP'
            respmsg += exp_id.to_bytes(2, 'little')
            
            # ok response
            responseObj = rsp.ResponseOKMessage(respmsg)
            
            
            runner = ExperimentsAvailable[exp_id]
            try:
                _thread.start_new_thread(runner, (ExpArgs, ERes,))
            except:
                # the only reason this might throw, afaik, is 
                # if something is already running on core1...
                # either way: not working out, return error instead
                responseObj = rsp.ResponseError(error_codes.UnterminatedCore1Experiment)
                
            queue_response(responseObj)
        elif typebyte == ord('P'):
            print("Ping")
            queue_response(rsp.ResponseOKMessage(payload))
        elif typebyte == ord('R'):
            print("Reboot")
            spasic.util.watchdog.force_reboot()
            queue_response(rsp.ResponseOK())

        elif typebyte == ord('S'):
            print("Status")
            queue_response(rsp.ResponseStatus(ERes.running, ERes.expid, ERes.exception_type_id,
                                              ERes.run_duration, ERes.result))
            
        elif typebyte == ord('T'):
            print("Clock")
            LastTimeSyncMessageTime = time.time()
            if len(payload) >= 4:
                LastTimeSyncValue = int.from_bytes(payload, 'little')
                print(f"time {LastTimeSyncValue}")
        


def get_i2c_device():
    # create our slave device
    i2c_dev = I2CDevice(address=sts.DeviceAddress, scl=sts.I2CSCL, sda=sts.I2CSDA,
                        baudrate=sts.I2CBaudRate)
    
    return i2c_dev

def main_loop():
    global PendingDataOut
    global ExperimentRun
    i2c_dev = get_i2c_device()
    # setup the callbacks
    i2c_dev.callback_data_in = i2c_data_in
    i2c_dev.callback_tx_done = tx_done_cb 
    i2c_dev.callback_tx_buffer_empty = tx_buffer_empty_cb
    
    # init the i2c device and start listening
    print("i2c:")
    if i2c_dev.begin():
        print("  success")
    else:
        print("  init?")
    
    micropython.mem_info()
    while True:
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
            if ExperimentRun:
                if not ERes.running:
                    # experiment is done!
                    ExperimentRun = False 
                    print("exp done, queue result")
                    queue_response(rsp.ResponseExperiment(ERes.expid, ERes.completed, 
                                                          ERes.exception_type_id, 
                                                          ERes.result))
            
            
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
            for outbytes in PendingDataOut:
                out_data += outbytes
            
            # reset the global out data list
            PendingDataOut = []
            
            # if we have some out data, shoot that 
            # off to the device so it can feed it 
            # out to master as it requests it
            if len(out_data):
                print(f"data out: {out_data}")
                i2c_dev.queue_outdata(out_data)
                
            i2c_dev.push_outgoing_data()
            
            # sleep a bit to yield so under the hood
            # magiks can happen if required
            time.sleep_ms(5)
                
        except Exception as e:
            print(f'ml ex: {e}')
            # report this unexpected error
            # but don't send a storm of them, if something 
            # goes terribly wrong
            if (out_queue_length() < 6 and i2c_dev.outdata_queue_size < (16*5)):
                except_id = ExpResult.exception_to_id(e)
                
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


    




