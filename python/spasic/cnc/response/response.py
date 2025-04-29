'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

class Response:
    def __init__(self):
        self.bytes = bytearray()
        
    def append(self, bts:bytearray):
        if isinstance(bts, int):
            try:
                v = bts % 256
                self.bytes += v.to_bytes()
            except:
                print(f"Prob appnd {bts}")
        elif isinstance(bts, list):
            try:
                self.bytes += bytearray(bts)
            except:
                print(f"Prob appnd {bts}") 
        else:
            try:
                self.bytes += bts 
            except:
                print(f"Prob appnd {bts}") 
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.bytes}>'
    
    def __str__(self):
        return f'{self.__class__.__name__} Response: {self.bytes}'
    
class ResponseOK(Response):
    '''
        OK
        0x01 0x01 b'OK'
    '''
    def __init__(self):
        super().__init__()
        self.append(b'\x01\x01OK')
        
class ResponseOKMessage(Response):
    '''
        OKMessage
        0x01 0x01 b'OK' LEN MSGBYTES
    '''
    def __init__(self, msg:bytearray):
        super().__init__()
        self.append(b'\x01\x02OK')
        if msg is not None and len(msg):
            self.append(len(msg))
            self.append(msg)
        else:
            self.append(0)
        
        
class ResponseError(Response):
    '''
        ERROR
        0x01 0x00 ERRORCODE ERRLEN BYTES[0:ERRLEN]
    '''
    def __init__(self, err_code:int, err_bts:bytearray=None):
        super().__init__()
        self.append(b'\x01\x00')
        self.append(err_code)
        if err_bts is not None and len(err_bts):
            self.append(len(err_bts))
            self.append(err_bts)
        else:
            self.append(0)
            
class ResponseExperiment(Response):
    '''
        Response from experiment
        
        0x09 EXPERIMENTID LEN RESULTBYTES (number of bytes depends on experiment)
    '''
    def __init__(self, exp_id:int, result:bytearray):
        super().__init__()
        self.append(b'\x09')
        self.append(exp_id)
        if result is not None and len(result):
            if len(result) > 13:
                result = result[:13]
            self.append(len(result))
            self.append(result)
        else:
            self.append(0)
            
class ResponseStatus(Response):
    '''
        Status 
        0x07 [RUNNING] [EXPID] [RUNTIME 4bytes] [RESULT up to 8 bytes]
    '''
    def __init__(self, exp_running:bool, exp_id:int=0, exception_id:int=0, run_time_s:int=0, result:bytearray=None):
        super().__init__()
        if exp_running:
            self.append(b'\x07\x01')
        else:
            self.append(b'\x07\x00')
            
        self.append(exp_id.to_bytes(1, 'little'))
        self.append(exception_id.to_bytes(1, 'little'))
        self.append(run_time_s.to_bytes(4, 'little'))
        if result is not None and len(result):
            if len(result) > 8:
                self.append(result[:8])
            else:
                self.append(result)
        