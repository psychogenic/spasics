'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import time
class Response:
    def __init__(self):
        self.payload = bytearray()
        
    @property 
    def bytes(self):
        if len(self.payload):
            return self.Header + self.payload 
        return self.Header 
    
    def reset(self):
        self.payload = bytearray()
    def minPayloadSize(self, blk:bytearray):
        return 0 
    
    def parseFrom(self, blk:bytearray):
        num_bytes_in_header = len(self.Header)
        if len(blk) < num_bytes_in_header:
            raise ValueError('Not enough data in block')
        
        if blk[:num_bytes_in_header] != self.Header:
            raise ValueError('Invalid header found')
        
        blkPostHeader = blk[len(self.Header):]
        if self.minPayloadSize(blkPostHeader) > len(blkPostHeader):
            raise ValueError('Not enough data in payload')
        
        self.reset()
        return self.extractPayload(blkPostHeader)
    
    def extractPayload(self, blk:bytearray):
        return blk
    
    def append(self, bts:bytearray):
        if isinstance(bts, int):
            try:
                v = bts % 256
                self.payload += v.to_bytes(1, 'little')
            except:
                print(f"noapp {bts}")
        elif isinstance(bts, list):
            try:
                self.payload += bytearray(bts)
            except:
                print(f"noapp {bts}") 
        else:
            try:
                self.payload += bts 
            except:
                print(f"noapp {bts}") 
                
    def __len__(self):
        return len(self.Header) + len(self.payload)
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.bytes}>'
    
    def __str__(self):
        return f'{self.__class__.__name__} Response: {self.bytes}'
    
class ResponseOK(Response):
    # '''
    #     OK
    #     0x01 0x01 b'OK'
    # '''
    Header = b'\x01\x01OK'
    def __init__(self):
        super().__init__()
        
        
    def __str__(self):
        return f'<Response: OK>'
        
class ResponseOKMessage(Response):
    # '''
    #     OKMessage
    #     0x01 0x02 b'OK' LEN MSGBYTES
    # '''
    Header = b'\x01\x02OK'
    def __init__(self, msg:bytearray):
        super().__init__()
        self.message = msg
        if msg is not None and len(msg):
            self.append(len(msg))
            self.append(msg)
        else:
            self.append(0)
            
    
    def minPayloadSize(self, blk:bytearray):
        return blk[0] + 1
    
    def extractPayload(self, blk:bytearray):
        plen = blk[0]
        self.message = blk[1:plen+1]
        
        self.payload = bytearray(blk[0:plen+1])
        
        return blk[plen+1:]
        
    def __str__(self):
        return f'<Response: OK {self.message}>'
        
class ResponseError(Response):
    # '''
    #     ERROR
    #     0x01 0x00 ERRORCODE ERRLEN BYTES[0:ERRLEN]
    # '''
    Header = bytearray([0x01, 0])
    def __init__(self, err_code:int, err_bts:bytearray=None):
        super().__init__()
        self.code = err_code
        self.append( err_code )
        if err_bts is not None and len(err_bts):
            self.append(len(err_bts))
            self.append(err_bts)
            self.message = err_bts;
        else:
            self.append(0)
            self.message = b''
            
    def minPayloadSize(self, blk:bytearray):
        return blk[1] + 2
    
    def extractPayload(self, blk:bytearray):
        self.code = blk[0]
        errlen = blk[1]
        if errlen:
            self.message = blk[2:(errlen+2)]
        else:
            self.message = b''
        
        self.payload = bytearray(blk[0:errlen+2])
        
        return blk[errlen+2:]
            
    def __str__(self):
        return f'<ERROR {self.code} "{self.message}>'
    
class ResponseExperiment(Response):
    # '''
    #     Response from experiment
    #
    #     0x09 EXPERIMENTID COMPLETED EXCEPTID LEN RESULTBYTES (number of bytes depends on experiment)
    # '''
    Header = b'\x09'
    def __init__(self, exp_id:int, completed:bool, exception_id:int, result:bytearray):
        super().__init__()
        self.exp_id = exp_id
        self.completed = completed
        self.exception_id = exception_id
        self.result = result
        self.append(bytearray([exp_id, 1 if completed else 0, exception_id]))
        
        if result is not None and len(result):
            res_len = len(result)
            if  res_len > 11:
                res_len = 11
                result = result[:11]
            self.append(res_len)
            self.append(result)
        else:
            self.append(0)
    
    def minPayloadSize(self, blk:bytearray):
        if len(blk) < 4:
            return 4
        return blk[3] + 4
    
    def extractPayload(self, blk:bytearray):
        self.exp_id = blk[0]
        self.completed = True if blk[1] else False 
        self.exception_id = blk[2]
        result_len = blk[3]
        self.result = blk[4:4+result_len]
        self.payload = bytearray(blk[0:result_len+4])
        
        return blk[result_len+4:]

    def __str__(self):
        if self.exception_id:
            return f'<EXPERIMENT {self.exp_id} completed:{self.completed} EXCEPTION:{self.exception_id} {self.result}>'
        return f'<EXPERIMENT {self.exp_id} completed:{self.completed} result:{self.result}>'
class ResponseFile(Response):
    Header = b'F'
    def __init__(self, rtype:bytes, value:bytearray=None):
        super().__init__()
        self.append(rtype)
        if value is not None:
            self.append(value)
            
    
    def minPayloadSize(self, blk:bytearray):
        raise RuntimeError('TODO')
    
    def extractPayload(self, blk:bytearray):
        raise RuntimeError('TODO')
            
            
class ResponseStatus(Response):
    # '''
    #     Status 
    #     0x07 [RUNNING] [EXPID] [RUNTIME 4bytes] [RESULT up to 8 bytes]
    # '''
    Header = b'\x07'
    def __init__(self, exp_running:bool, exp_id:int=0, exception_id:int=0, run_time_s:int=0, result:bytearray=None):
        super().__init__()
        self.running = exp_running
        if exp_running:
            self.append(b'\x01')
        else:
            self.append(b'\x00')
            
        self.exp_id = exp_id
        self.exception_id = exception_id
        self.runtime = run_time_s
        self.result = result
        
        self.append(exp_id.to_bytes(1, 'little'))
        self.append(exception_id.to_bytes(1, 'little'))
        self.append(run_time_s.to_bytes(4, 'little'))
        
        if result is not None and len(result):
            if len(result) > 8:
                self.append(result[:8])
            else:
                self.append(result)
                
        
    def minPayloadSize(self, blk:bytearray):
        return 7
    
    def extractPayload(self, blk:bytearray):
        self.running = True if blk[0] else False
        self.exp_id = blk[1]
        self.exception_id = blk[2]
        self.runtime = int.from_bytes(blk[3:7], 'little')
        res_len = 0
        if len(blk) > 7:
            res_len = len(blk) - 7
            if res_len > 8:
                res_len = 8
        self.result = blk[7:(7+res_len)]
        
        self.payload = blk[0:(7+res_len)]
        
        # messup here, as I wanted as many bytes as possible but do not 
        # now how many result bytes there are, so we return "too many" leftovers 
        return blk[7+res_len:]

    def __str__(self):
        if self.exception_id:
            return f'<STATUS {self.exp_id} running:{self.running} EXCEPTION:{self.exception_id} runtime: {self.runtime}s {self.result}>'
        
        return f'<STATUS {self.exp_id} running:{self.running} runtime: {self.runtime}s {self.result}>'
        
    
class ResponseVariableValue(Response):
    Header = b'V'
    def __init__(self, vid:id, value:bytearray):
        super().__init__()
        self.append(vid)
        self.append(len(value))
        self.append(value)
        
        
    def minPayloadSize(self, blk:bytearray):
        if len(blk) < 2:
            return 2
        
        return blk[1] + 2
    
    def extractPayload(self, blk:bytearray):
        self.vid = blk[0]
        vlen = blk[1]
        self.value = blk[2:(2+vlen)]
        self.payload = blk[:(2+vlen)]
        return blk[(2+vlen):]
        
class ResponseDataBytes(Response):
    Header = b'D'
    def __init__(self, value:bytearray):
        super().__init__()
        self.append(len(value))
        self.append(value)
        
    def minPayloadSize(self, blk:bytearray):
        if len(blk) < 1:
            return 1
        
        return blk[0] + 1
    
    def extractPayload(self, blk:bytearray):
        dlen = blk[0]
        self.data = blk[1:(1+dlen)]
        self.payload = blk[:(1+dlen)]
        return blk[(1+dlen):]
        
        
class ResponseInfo(Response):
    Header = b'I'
    def __init__(self, v_maj:int, v_min:int, v_patch:int, v_comment:str, uptime:int, sync_time:int):
        super().__init__()
        bts = bytearray(11)
        bts[0:3] = bytearray([v_patch, v_min, v_maj])
        bts[3:7] = uptime.to_bytes(4, 'little')
        bts[7:11] = sync_time.to_bytes(4, 'little')
        
        if len(v_comment):
            bts += bytearray(v_comment, 'ascii')
            
        self.v_patch = v_patch
        self.v_min = v_min
        self.v_maj = v_maj
        self.uptime = uptime
        self.synctime = sync_time
        self.append(bts)
        

        
    def minPayloadSize(self, blk:bytearray):
        return 11
    
    def extractPayload(self, blk:bytearray):
        self.v_patch = blk[0]
        self.v_min = blk[1]
        self.v_maj = blk[2]
        self.uptime = int.from_bytes(blk[3:(3+4)], 'little')
        self.synctime = int.from_bytes(blk[7:(7+4)], 'little')
        
        self.payload = blk[:11]
        return blk[11:]

    def __str__(self):
        #t = time.gmtime(self.uptime)
        #uptime = f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        
        t = time.gmtime(self.synctime)
        synctime = f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        return f'<INFO v{self.v_maj}.{self.v_min}.{self.v_patch} synctime {synctime}>'
    
class ResponseFactory:
    def __init__(self):
        pass 
    
    @classmethod
    def constructFrom(cls, blk):
        if not len(blk):
            return None
        idx = 0
        while idx < len(blk) and blk[idx] == 0:
            idx += 1
        if idx:
            blk.consume(idx)
        if not len(blk):
            return None
        
        rPoss = [
                ResponseOK(),
                ResponseOKMessage(b''),
                ResponseDataBytes(b''),
                ResponseError(0, b''),
                ResponseExperiment(0, False, 0, b''),
                ResponseFile(b''),
                ResponseInfo(0,0,0,'', 0, 0),
                ResponseStatus(False, 0, 0, 0),
                ResponseVariableValue(0, b'')
            ]
        
        for rt in rPoss:
            try:
                rt.parseFrom(blk)
                blk.consume(len(rt))
                # print(f"Parsed a {rt} from block, {len(blk)} leftover")
                return rt
            except ValueError:
                # print(f"Parsing {blk} didn't work out")
                pass
        
        #print(f'Could not get a match for {blk}')
        if len(blk) > 16:
            print(f"Could not get a match, dropping a byte from {blk}")
            blk = blk.consume(1)
            # we're loosing a msg because of parse (see ResponseStatus) advance one byte and try again
            
        return None

        