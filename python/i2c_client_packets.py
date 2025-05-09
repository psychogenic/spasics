# translations from spasic.error_codes
ErrorCodes = {
    
    0x01: 'Unknown Command',
    0x02: 'Unknown Experiment',
    0x03: 'Busy',
    0x04: 'Unterminated Core1 Exp',
    0x05: 'Runtime Exception',
    0x06: 'Invalid Request',
    0x07: 'Unknown Variable',
    0x08: 'Cannot open file',
    0x09: 'EOF',
    0x0A: 'Write Failure',
    0x0B: 'MakeDir Failure',
    0x0C: 'Delete File Failure',
    0x0D: 'Rename File Failure',
    0x0E: 'POST Fail'
}

class ClientPacketGenerator:
    
    def __init__(self):
        pass 
    
    def abort(self):
        return  bytearray([ord('A')])
        
    def time_sync(self, t_now:int):
        bts = bytearray([ord('T')])
        bts += t_now.to_bytes(4, 'little')
        return bts
    
    def status(self):
        return  bytearray([ord('S')])
    
    def ping(self, count:int, extra_payload=b'PNG'):
        bts = bytearray([ord('P'), count % 256])
        bts += extra_payload
        return bts
    
    def info(self):
        return bytearray([ord('I')])
    
    
    def reboot(self, safe_mode:bool=False):
        return bytearray([ord('R'), 1 if safe_mode else 0])

    def experiment_result(self):
        return bytearray([ord('E') + ord('I')])
        
    def run_experiment_now_list(self, experiment_id:int, args:bytearray=None):
        
        ret_list = []
        if args is not None and len(args):
            for chunk in [args[i:i + 7] for i in range(0, len(args), 7)]:
                bts = bytearray([ord('E') + ord('A')])
                bts.extend(chunk)
                ret_list.append(bts)
        
        bts = bytearray([ord('E')])
        bts += experiment_id.to_bytes(2, 'little')
        ret_list.append(bts)
        return ret_list
    
    def filesize(self, varid:int):
            return bytearray([ord('F'), ord('S'), varid])
            
    def mkdir(self, varid:int):
        return bytearray([ord('F'), ord('D'), varid])
    def lsdir(self, varid:int):
        return bytearray([ord('F'), ord('L'), varid])
    
    def file_unlink(self, varid:int):
        return bytearray([ord('F'), ord('U'), varid])
    
    def file_move(self, srcvarid:int, destvarid:int):
        return bytearray([ord('F'), ord('M'), srcvarid, destvarid])
        
    def open_read(self, varid:int):
        return bytearray([ord('F'), ord('O'), varid, ord('R')])
    
    def file_close(self):
        return bytearray([ord('F') + ord('C')])
        
    def file_read(self, num_bytes:int=0):
        if num_bytes:
            return bytearray([ord('F') + ord('R'), num_bytes % 256])
        else:
            return bytearray([ord('F') + ord('R')])
            
    def file_write_list(self, bts_to_write:bytearray):
        cmdPrefix = ord('F') + ord('W')
        ret_list = []
        for chunk in [bts_to_write[i:i + 7] for i in range(0, len(bts_to_write), 7)]:
            vals = [cmdPrefix]
            vals.extend(chunk)
            ret_list.append(bytearray(vals)) 
        return ret_list  
    def open_write(self, varid:int):
        return bytearray([ord('F'), ord('O'), varid, ord('W')])
    
    def checksum(self, varid:int):
        return bytearray([ord('F'), ord('Z'), varid])
    def getvar(self, v:int):
        return bytearray([ord('V'), v])
    
    def setvar_list(self, v:int, val):
        if isinstance(val, str):
            val = bytearray(val, 'ascii')
        
        chunks = [val[i:i + 6] for i in range(0, len(val), 6)]
        
        setvar = bytearray([ord('V') + ord('S'), v])
        setvar.extend(chunks[0])
        
        ret_list = [setvar]
        if len(chunks) == 1:
            return ret_list
        
        for i in range(1, len(chunks)):
            appvar = bytearray([ord('V') + ord('A'), v])
            appvar.extend(bytearray(chunks[i]))
            ret_list.append(appvar)
            
        return ret_list
            
    
    