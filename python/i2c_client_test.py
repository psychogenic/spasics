'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import machine 
import time 
import random

SlaveAddress = 0x51 
ResponseDelaySeconds = 0.5

class SatelliteSimulator:
    '''
        Talks to spasics satellite board over I2C
        and knows how to craft message and interpret 
        data coming back.
    '''
    def __init__(self, scl:int=25, sda:int=24, baudrate:int=100000):
        self._i2c = machine.I2C(0, scl, sda, freq=baudrate)
        self._start_time = time.time()
        self._ping_count = 0
        
    def send(self, bts:bytearray):
        '''
            send raw bytes over to device
        '''
        self._i2c.writeto(SlaveAddress, bts)
        
    def read_block(self):
        '''
            read a block of 16 bytes from device
        '''
        return self._i2c.readfrom(SlaveAddress, 16)
    
    def read_pending(self):
        '''
            read blocks of 16 bytes until you hit 
            and "empty" response (all 0xff)
            and interpret the data
        '''
        empty = bytearray([0xff]*16)
        
        rcvd = []
        while True:
            # read til empty
            blk = self.read_block()
            if blk == empty:
                if not len(rcvd):
                    # first is empty
                    return 'EMPTY'
                if len(rcvd) == 1:
                    return rcvd[0] 
                return rcvd
            
            
            elif blk[0] == 0x01:
                # system message: 0x01 ...
                if blk[1]:
                    # ok message: 0x01 [NON-ZERO] ...
                    if blk[1] == 0x01:
                        # 0x01 0x01 : OK
                        return 'OK'
                    if blk[1] == 0x02:
                        # 0x01 0x2 LEN MSG[LEN]: OK WITH PAYLOAD
                        msglen = blk[4]
                        msg = blk[5:(5+msglen)]
                        rcvd.append( f'OK: {msg}' )
                else:
                    # error message
                    # 0x01 0x00 ERRCODE LEN MSG[LEN]
                    errcode = blk[2]
                    errlen = blk[3]
                    if errlen:
                        errmsg = blk[3:(3+errlen)]
                    else:
                        errmsg = ''
                    rcvd.append( f'ERROR [{errcode}] {errmsg}' )
            
            elif blk[0] == 0x07:
                # 0x07 RUNNING EXPERIMENTID EXCEPTIONID RUNTIME[4] RESULT[8]
                running = True if blk[1] else False
                expid = blk[2]
                exception_id = blk[3]
                runtime = int.from_bytes(blk[4:(4+4)], 'little')
                res = blk[8:]
                if exception_id:
                    exstr = f'Exception: {exception_id}'
                else:
                    exstr = 'OK'
                rcvd.append( f'Status running:{running} exp {expid} {exstr} {runtime}s: {res}')
            
                
            elif blk[0] == 0x09:
                # 0x09 EXPERIMENTID COMPLETED EXCEPT_ID LEN RESULTBYTES[LEN]
                expid = blk[1]
                completed = blk[2]
                except_id = blk[3]
                reslen = blk[4]
                if reslen:
                    resmsg = blk[5:(5+reslen)]
                else:
                    resmsg = ''
                
                end_status = ''
                if except_id:
                    end_status = f'Exception {except_id}'
                else:
                    if completed:
                        end_status = 'COMPLETED'
                    else:
                        end_status = 'INCOMPLETED?'
                    
                    
                rcvd.append( f'EXPERIMENT {expid}: {end_status} {resmsg}' )
            else:
                rcvd.append(f"Unknown response: {blk}")
        
    
    def abort(self):
        # b'A'
        print("Requesting experiment abort")
        bts = bytearray([ord('A')])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
        
    def time_sync(self):
        # 'T' and 4 bytes of time
        t_now = time.time() - self._start_time
        bts = bytearray([ord('T')])
        bts += t_now.to_bytes(4, 'little')
        print(f"Sending time sync {t_now}")
        self.send(bts)
        
    def status(self):
        # b'S'
        print("Requesting status")
        bts = bytearray([ord('S')])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def ping(self):
        # 'P' and payload byte to get back in pong
        self._ping_count += 1
        print(f"Sending ping {self._ping_count}")
        bts = bytearray([ord('P'), self._ping_count % 256])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def reboot(self, safe_mode:bool=False):
        # 'R' and one byte (safemode, unimplemented)
        print(f"Sending reboot command")
        bts = bytearray([ord('R'), 1 if safe_mode else 0])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def run_experiment_now(self, experiment_id:int, args:bytearray=None):
        # 'E' EXPID[2]
        print(f"Requesting run of experiment {experiment_id}")
        bts = bytearray([ord('E')])
        bts += experiment_id.to_bytes(2, 'little')
        if args:
            bts += args
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
        
        
def pingit():
    while True:
        sim.ping()
        time.sleep(0.3)

def random_exp2_params():
    sub_exp = random.randint(0,1)
    iters = random.randint(2, 12)
    print(f"Running {sub_exp} {iters} times")
    return bytearray([iters, sub_exp])
    
StressCount = 0
def stressTest():
    global StressCount 
    StressCount = 0
    while True:
        StressCount += 1
        
        
        sim.run_experiment_now(2, random_exp2_params())
        sim.status()
        sim.ping()
        sim.status()
        sim.ping()
        sim.status()
        time.sleep(1)
        sim.run_experiment_now(1)
        sim.ping()
        sim.status()
        sim.ping()
        sim.status()
        sim.ping()
        time.sleep(1.3)
        sim.status()
        sim.run_experiment_now(2, random_exp2_params())
        time.sleep(1)
        sim.status()
        time.sleep(4)
        sim.status()
        sim.run_experiment_now(2, random_exp2_params())
        sim.status()
        time.sleep(1)
        sim.status()
        

        
if __name__ == '__main__':
    sim = SatelliteSimulator()
    
        