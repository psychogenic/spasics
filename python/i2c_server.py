'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


import time
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

ERes = ExpResult()
ExpArgs = ExperimentParameters(DemoBoard.get())




def tx_done_cb():
    print('i2c tx done')
    
def tx_buffer_empty_cb():
    print('i2c buffer empty')


PendingDataIn = [bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8)]
PendingDataNum = 0

PendingDataOut = []
def i2c_data_in(numbytes:int, bts:bytearray):
    global PendingDataIn 
    global PendingDataNum
    print(f"IN {bts}")
    if len(bts):
        for i in range(numbytes):
            PendingDataIn[PendingDataNum][i] = bts[i]
        PendingDataNum += 1
            
        # PendingDataIn.append(bytearray(bts))


def queue_response(response:rsp.Response):
    global PendingDataOut
    PendingDataOut.append(response.bytes)
    
def get_and_flush_pending_in():
    global PendingDataIn, PendingDataNum
    # machine.disable_irq()
    if not PendingDataNum:
        # machine.enable_irq()
        return []
    
    # race condition ?
    data_rcvd = list(PendingDataIn)
    PendingDataNum = 0
    #machine.enable_irq()
    return data_rcvd 

def process_pending_data():
    data_rcvd = get_and_flush_pending_in()
    if not len(data_rcvd):
        return 0

    
    for bts in data_rcvd:
        typebyte = bts[0]
        payload = bts[1:]
        if typebyte == ord('A'):
            print("Abort any experiment")
            ExpArgs.terminate()
            if ERes.running:
                respmsg = b'TRM'
                respmsg += ERes.expid.to_bytes(2, 'little')
                queue_response(rsp.ResponseOKMessage(respmsg))
            else:
                queue_response(rsp.ResponseOK())
                
        elif typebyte == ord('E'):
            print("Run experiment")
                
            if ERes.running:
                queue_response(rsp.ResponseError(error_codes.Busy, 
                                                      ERes.expid.to_bytes(2, 'little')))
                return 
            
            
            if len(payload):
                exp_id = int.from_bytes(payload, 'little')
            else:
                exp_id = 0
                
            if exp_id not in ExperimentsAvailable:
                queue_response(rsp.ResponseError(error_codes.UnknownExperiment, bytearray([exp_id])))
                return 
            
            
            ERes.expid = exp_id
            ERes.start()
            ExpArgs.start()
            runner = ExperimentsAvailable[exp_id]
            
            _thread.start_new_thread(runner, (ExpArgs, ERes,))
            
            respmsg = b'EXP'
            respmsg += exp_id.to_bytes(2, 'little')
            queue_response(rsp.ResponseOKMessage(respmsg))
        elif typebyte == ord('P'):
            print("Ping")
            queue_response(rsp.ResponseOKMessage(payload))
        elif typebyte == ord('R'):
            print("Reboot")
            queue_response(rsp.ResponseOK())

        elif typebyte == ord('S'):
            print("Get Status")
            queue_response(rsp.ResponseStatus(ERes.running, ERes.expid, ERes.exception_type_id,
                                              ERes.run_duration, ERes.result))
            
        elif typebyte == ord('T'):
            print("Sys Clock")
            if len(payload) >= 4:
                tnow = int.from_bytes(payload, 'little')
                print(f"Set time to {tnow}")
        


def get_i2c_device():
    # create our slave device
    i2c_dev = I2CDevice(address=sts.DeviceAddress, scl=sts.I2CSCL, sda=sts.I2CSDA,
                        baudrate=sts.I2CBaudRate)
    
    return i2c_dev

def main_loop():
    global PendingDataOut
    print("Entering main loop")
    i2c_dev = get_i2c_device()
    # setup the callbacks
    i2c_dev.callback_data_in = i2c_data_in
    i2c_dev.callback_tx_done = tx_done_cb 
    i2c_dev.callback_tx_buffer_empty = tx_buffer_empty_cb
    
    # init the i2c device and start listening
    print("Starting i2c device:")
    if i2c_dev.begin():
        print("  success")
    else:
        print("  already init?")
    
    while True:
        try:
            
            # may have queued data received from 
            # master side, process that into commands
            # print(".", end='')
            # time.sleep(0.02)
            
            i2c_dev.poll_pending_data()
            num_incoming = process_pending_data()
            if num_incoming:
                print(f"Processed {num_incoming} messages")
            out_data = bytearray()
            for outbytes in PendingDataOut:
                out_data += outbytes
            
            PendingDataOut = []
            
            # time.sleep(0.02)
            if len(out_data):
                print(f"Have data to send: {out_data}")
                i2c_dev.queue_outdata(out_data)
                
            i2c_dev.push_outgoing_data()
                
            time.sleep_ms(5)
                
        except Exception as e:
            print(f'ml ex: {e}')
            raise e


    




