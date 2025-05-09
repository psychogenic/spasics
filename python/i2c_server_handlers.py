'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
import i2c_server_globals as i2cglb

import spasic.cnc.response.response as rsp
import spasic.error_codes as error_codes

def queue_response(response:rsp.Response):
    i2cglb.PendingDataOut.append(response.bytes)
    

def abort():
    i2cglb.ExpArgs.terminate()
    if i2cglb.ERes.running:
        respmsg = b'TRM'
        respmsg += i2cglb.ERes.expid.to_bytes(2, 'little')
        queue_response(rsp.ResponseOKMessage(respmsg))
    else:
        queue_response(rsp.ResponseOK())
def fs_file_close():
    if i2cglb.FileSystem.close():
        queue_response(rsp.ResponseOKMessage(b'CLS'))
    else:
        queue_response(rsp.ResponseError(error_codes.InvalidRequest, b'NOFL?'))
        
def fs_file_read(payload:bytearray):
    # TODO:FIXME how much data should we queue per request?
    read_size = 16*4 - 2
    if len(payload) > 0:
        if payload[0]:
            read_size = payload[0]
    
    # print(f"fread {read_size}")
    dat = i2cglb.FileSystem.read_bytes(read_size)
    if not len(dat):
        return queue_response(rsp.ResponseError(error_codes.EndOfFile))
    
    queue_response(rsp.ResponseDataBytes(dat))
    
def fs_file_write(payload:bytearray):
    # TODO:FIXME how much data should we queue per request?
    print(f"fwr {payload}")
    if len(payload) < 1:
        print("payload empty -- ignore!")
        return 
        # return queue_response(invalidReq)
    
    if not i2cglb.FileSystem.write_bytes(payload):
        print("WRITE FAILURE")
        # probably don't want to queue errors, 
        # we might end up with a storm
        # queue_response(rsp.ResponseError(error_codes.WriteFailure))
    
def fs_action_on_vid(payload:bytearray):
    # b'FS' VARID -- read size
    # b'FZ' VARID -- read checksum
    # b'FO' VARID 'R'|'W' -- open for read or write
    # b'FD' VARID -- make a directory (including parents)
    # b'FU' VARID -- unlink/delete a file
    # b'FM' SRCVARID DESTVARID -- move SRC to DEST
    # b'FL' VARID -- ls
    invalidReq = rsp.ResponseError(error_codes.InvalidRequest)
    if len(payload) < 2:
        return queue_response(invalidReq)
    
    action = payload[0]
    vid = payload[1]
    if not i2cglb.ClientVariables.has(vid):
        return queue_response(rsp.ResponseError(error_codes.UnknownVariable))
    
    filepath = i2cglb.ClientVariables.get_string(vid)
    print(f"file action {action} on {filepath}")
    if action == ord('S'):
        sz = i2cglb.FileSystem.file_size(filepath)
        queue_response(rsp.ResponseFile(b'SZ', sz.to_bytes(4, 'little')))
    elif action == ord('Z'):
        cs = i2cglb.FileSystem.simple_checksum(filepath)
        queue_response(rsp.ResponseFile(b'CS', cs.to_bytes(4, 'little')))
        
    elif action == ord('D'):
        print("mkdir")
        if i2cglb.FileSystem.mkdir(filepath):
            queue_response(rsp.ResponseOKMessage(b'MKDIR'))
        else:
            queue_response(rsp.ResponseError(error_codes.MakeDirFailure, bytearray([vid])))
    elif action == ord('L'):
        print("LS")
        dirs = i2cglb.FileSystem.lsdir(filepath)
        if not len(dirs):
            queue_response(rsp.ResponseError(error_codes.CantOpenFile, b'BDDIR'))
            return 
        for chunk in [dirs[i:i + 14] for i in range(0, len(dirs), 14)]:
            try:
                queue_response(rsp.ResponseFile(b'D', bytearray(chunk, 'ascii')))
            except:
                pass
    elif action == ord('U'):
        print("DEL!")
        if i2cglb.FileSystem.delete(filepath):
            queue_response(rsp.ResponseOKMessage(b'RM'))
        else:
            queue_response(rsp.ResponseError(error_codes.DeleteFileFailure, bytearray([vid])))
    elif action == ord('M'):
        
        if len(payload) < 3:
            return queue_response(invalidReq)
        
        destvid = payload[2]
        if not i2cglb.ClientVariables.has(destvid):
            return queue_response(rsp.ResponseError(error_codes.UnknownVariable))
        
        destpath = i2cglb.ClientVariables.get_string(destvid)
        print(f"mv {filepath} {destpath}")
        if i2cglb.FileSystem.move(filepath, destpath):
            queue_response(rsp.ResponseOKMessage(b'MV'))
        else:
            queue_response(rsp.ResponseError(error_codes.RenameFileFailure))
    elif action == ord('O'):
        if len(payload) < 3:
            return queue_response(invalidReq)
        rw = payload[2]
        if rw == ord('R'):
            print("oread")
            if not i2cglb.FileSystem.open_for_read(filepath):
                return queue_response(rsp.ResponseError(error_codes.CantOpenFile))
        elif rw == ord('W'):
            print("owrite")
            if not i2cglb.FileSystem.open_for_write(filepath):
                return queue_response(rsp.ResponseError(error_codes.CantOpenFile))
            pass 
        else:
            return queue_response(invalidReq)

def variable_get(payload:bytearray):
    if len(payload) < 1:
        queue_response(rsp.ResponseError(error_codes.InvalidRequest))
        return
    vid = payload[0]
    if not i2cglb.ClientVariables.has(vid):
        queue_response(rsp.ResponseError(error_codes.UnknownVariable, bytearray([vid])))
        return
    queue_response(rsp.ResponseVariableValue(vid, i2cglb.ClientVariables.get_bytearray(vid)))

def variable_set(payload:bytearray):
    if len(payload) < 1:
        queue_response(rsp.ResponseError(error_codes.InvalidRequest))
        return
    vid = payload[0]
    if len(payload) < 2:
        print("Setting to empty")
        i2cglb.ClientVariables.set(vid, bytearray())
    else:
        print(f"Setting to {payload[1:]}")
        i2cglb.ClientVariables.set(vid, payload[1:])
        
    queue_response(rsp.ResponseOK())
    
def variable_append(payload:bytearray):
    if len(payload) < 2:
        queue_response(rsp.ResponseError(error_codes.InvalidRequest))
        return
    vid = payload[0]
    if not i2cglb.ClientVariables.has(vid):
        queue_response(rsp.ResponseError(error_codes.UnknownVariable, bytearray([vid])))
        return
        
    i2cglb.ClientVariables.append(vid, payload[1:])
    
def time_sync(payload:bytearray):
    i2cglb.LastTimeSyncMessageTime = time.time()
    if len(payload) >= 4:
        i2cglb.LastTimeSyncValue = int.from_bytes(payload, 'little')
        print(f"time {i2cglb.LastTimeSyncValue}")