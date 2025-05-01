'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import time
import gc
import micropython
import machine
import _thread
from spasic.fs.filesystem import FSAccess
import spasic.cnc.response.response as rsp
import spasic.settings as sts
from spasic.variables.variables import Variables


if sts.DebugUseSimulatedI2CDevice:
    from spasic.i2c.device_sim import I2CDevice
else:
    from spasic.i2c.device import I2CDevice
    
import spasic.error_codes as error_codes
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters
from spasic.experiment.experiment_list import ExperimentsAvailable
from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
import spasic.util.watchdog

FileSystem = FSAccess()
ERes = ExpResult()
ExpArgs = ExperimentParameters(DemoBoard.get())




def tx_done_cb():
    pass # print('i2c tx done')
    
def tx_buffer_empty_cb():
    pass # print('i2c buffer empty')

ClientVariables = Variables()

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
            
            # always ensure we start fresh in ASIC_RP_CONTROL mode,
            # just in case an experiment messed with it.
            DemoBoard.get().mode = RPMode.ASIC_RP_CONTROL
            
            runner = ExperimentsAvailable[exp_id]
            try:
                _thread.start_new_thread(runner, (ExpArgs, ERes,))
            except:
                # the only reason this might throw, afaik, is 
                # if something is already running on core1...
                # either way: not working out, return error instead
                responseObj = rsp.ResponseError(error_codes.UnterminatedCore1Experiment, b'CORBZY')
                
            queue_response(responseObj)
            
        elif typebyte == ord('F'):
            # b'FS' VARID -- read size
            # b'FZ' VARID -- read checksum
            # b'FO' VARID 'R'|'W' -- open for read or write
            # b'FD' VARID -- make a directory (including parents)
            # b'FU' VARID -- unlink/delete a file
            # b'FM' SRCVARID DESTVARID -- move SRC to DEST
            
            invalidReq = rsp.ResponseError(error_codes.InvalidRequest)
            if len(payload) < 2:
                return queue_response(invalidReq)
            
            action = payload[0]
            vid = payload[1]
            if not ClientVariables.has(vid):
                return queue_response(rsp.ResponseError(error_codes.UnknownVariable))
            
            filepath = ClientVariables.get_string(vid)
            print(f"file action {action} on {filepath}")
            if action == ord('S'):
                sz = FileSystem.file_size(filepath)
                queue_response(rsp.ResponseOKMessage(b'SZ' + sz.to_bytes(4, 'little')))
            elif action == ord('Z'):
                cs = FileSystem.simple_checksum(filepath)
                queue_response(rsp.ResponseOKMessage(b'CS' + cs.to_bytes(4, 'little')))
                
            elif action == ord('D'):
                print("mkdir")
                if FileSystem.mkdir(filepath):
                    queue_response(rsp.ResponseOKMessage(b'MKDIR'))
                else:
                    queue_response(rsp.ResponseError(error_codes.MakeDirFailure, bytearray([vid])))
            elif action == ord('U'):
                print("DEL!")
                if FileSystem.delete(filepath):
                    queue_response(rsp.ResponseOKMessage(b'RM'))
                else:
                    queue_response(rsp.ResponseError(error_codes.DeleteFileFailure, bytearray([vid])))
            elif action == ord('M'):
                
                if len(payload) < 3:
                    return queue_response(invalidReq)
                
                destvid = payload[2]
                if not ClientVariables.has(destvid):
                    return queue_response(rsp.ResponseError(error_codes.UnknownVariable))
                
                destpath = ClientVariables.get_string(destvid)
                print(f"mv {filepath} {destpath}")
                if FileSystem.move(filepath, destpath):
                    queue_response(rsp.ResponseOKMessage(b'MV'))
                else:
                    queue_response(rsp.ResponseError(error_codes.RenameFileFailure))
            elif action == ord('O'):
                if len(payload) < 3:
                    return queue_response(invalidReq)
                rw = payload[2]
                if rw == ord('R'):
                    print("oread")
                    if not FileSystem.open_for_read(filepath):
                        return queue_response(rsp.ResponseError(error_codes.CantOpenFile))
                elif rw == ord('W'):
                    print("owrite")
                    if not FileSystem.open_for_write(filepath):
                        return queue_response(rsp.ResponseError(error_codes.CantOpenFile))
                    pass 
                else:
                    return queue_response(invalidReq)
        elif typebyte == ord('F') + ord('C'):
            print("file close")
            if FileSystem.close():
                queue_response(rsp.ResponseOKMessage(b'CLS'))
            else:
                queue_response(rsp.ResponseError(error_codes.InvalidRequest, b'NOFL?'))
                
        elif typebyte == ord('F') + ord('R'):
            # TODO:FIXME how much data should we queue per request?
            read_size = 16*4 - 2
            if len(payload) > 0:
                if payload[0]:
                    read_size = payload[0]
            
            print(f"fread {read_size}")
            dat = FileSystem.read_bytes(read_size)
            if not len(dat):
                return queue_response(rsp.ResponseError(error_codes.EndOfFile))
            
            queue_response(rsp.ResponseDataBytes(dat))
            
        elif typebyte == ord('F') + ord('W'):
            # TODO:FIXME how much data should we queue per request?
            print(f"fwrite {payload}")
            if len(payload) < 1:
                return queue_response(invalidReq)
            
            if not FileSystem.write_bytes(payload):
                print("WRITE FAILURE")
                # probably don't want to queue errors, 
                # we might end up with a storm
                # queue_response(rsp.ResponseError(error_codes.WriteFailure))
            
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
        elif typebyte == ord('V'):
            print("Get variable")
            if len(payload) < 1:
                queue_response(rsp.ResponseError(error_codes.InvalidRequest))
                return
            vid = payload[0]
            if not ClientVariables.has(vid):
                queue_response(rsp.ResponseError(error_codes.UnknownVariable, bytearray([vid])))
                return
            queue_response(rsp.ResponseVariableValue(vid, ClientVariables.get_bytearray(vid)))
                
        
        elif typebyte == ord('V') + ord('S'):
            print("Set variable")
            if len(payload) < 1:
                queue_response(rsp.ResponseError(error_codes.InvalidRequest))
                return
            vid = payload[0]
            if len(payload) < 2:
                print("Setting to empty")
                ClientVariables.set(vid, bytearray())
            else:
                print(f"Setting to {payload[1:]}")
                ClientVariables.set(vid, payload[1:])
                
            queue_response(rsp.ResponseOK())
            
        elif typebyte == ord('V') + ord('A'):
            print("Append variable")
            if len(payload) < 2:
                queue_response(rsp.ResponseError(error_codes.InvalidRequest))
                return
            vid = payload[0]
            if not ClientVariables.has(vid):
                queue_response(rsp.ResponseError(error_codes.UnknownVariable, bytearray([vid])))
                return
                
            ClientVariables.append(vid, payload[1:])

_I2CDevSingleton = None
def get_i2c_device():
    global _I2CDevSingleton
    if _I2CDevSingleton is None:
        # create our slave device
        _I2CDevSingleton = I2CDevice(address=sts.DeviceAddress, scl=sts.I2CSCL, sda=sts.I2CSDA,
                        baudrate=sts.I2CBaudRate)
    
    return _I2CDevSingleton

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

def main_loop(runtimes:int=0):
    global PendingDataOut
    global ExperimentRun
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
                if sts.DebugUseSimulatedI2CDevice:
                    raise e


    




