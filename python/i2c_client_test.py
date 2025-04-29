'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import machine 
import time 

SlaveAddress = 0x51 
ResponseDelaySeconds = 0.5

class SatelliteSimulator:
    
    def __init__(self, scl:int=25, sda:int=24, baudrate:int=100000):
        self._i2c = machine.I2C(0, scl=25, sda=24, freq=100000)
        self._start_time = time.time()
        self._ping_count = 0
        
    def send(self, bts:bytearray):
        self._i2c.writeto(SlaveAddress, bts)
        
    def read_block(self):
        return self._i2c.readfrom(SlaveAddress, 16)
    
    def read_pending(self):
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
            
            # print(f"Got data block {blk}")
            elif blk[0] == 0x01:
                # system message
                if blk[1]:
                    # ok message
                    if blk[1] == 0x01:
                        return 'OK'
                    if blk[1] == 0x02:
                        msglen = blk[4]
                        msg = blk[5:(5+msglen)]
                        rcvd.append( f'OK: {msg}' )
                else:
                    # error message
                    errcode = blk[2]
                    errlen = blk[3]
                    if errlen:
                        errmsg = blk[3:(3+errlen)]
                    else:
                        errmsg = ''
                    rcvd.append( f'ERROR [{errcode}] {errmsg}' )
            
            elif blk[0] == 0x07:
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
                # 0x09 EXPERIMENTID LEN RESULTBYTES (number of bytes depends on experiment)
                expid = blk[1]
                reslen = blk[2]
                if reslen:
                    resmsg = blk[2:(2+reslen)]
                else:
                    resmsg = ''
                    
                rcvd.append( f'EXPERIMENT {expid}: {resmsg}' )
            else:
                rcvd.append(f"Unknown response: {blk}")
        
    
    def abort(self):
        print("Requesting experiment abort")
        bts = bytearray([ord('A')])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
        
    def time_sync(self):
        t_now = time.time() - self._start_time
        bts = bytearray([ord('T')])
        bts += t_now.to_bytes(4, 'little')
        print(f"Sending time sync {t_now}")
        self.send(bts)
        
    def status(self):
        print("Requesting status")
        bts = bytearray([ord('S')])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def ping(self):
        self._ping_count += 1
        print(f"Sending ping {self._ping_count}")
        bts = bytearray([ord('P'), self._ping_count % 256])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def reboot(self, safe_mode:bool=False):
        print(f"Sending reboot command")
        bts = bytearray([ord('R'), 1 if safe_mode else 0])
        self.send(bts)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def run_experiment_now(self, experiment_id:int, args:bytearray=None):
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

StressCount = 0
def stressTest():
    global StressCount 
    StressCount = 0
    while True:
        StressCount += 1
        sim.run_experiment_now(1)
        sim.run_experiment_now(2)
        sim.status()
        sim.ping()
        sim.status()
        sim.ping()
        sim.status()
        sim.ping()
        sim.status()
        sim.ping()
        sim.status()
        sim.ping()
        time.sleep(0.8)
        sim.status()
        sim.run_experiment_now(2)
        time.sleep(1)
        sim.status()
        time.sleep(4)
        sim.status()
        sim.run_experiment_now(2)
        sim.status()
        time.sleep(1)
        sim.status()
        

        
if __name__ == '__main__':
    sim = SatelliteSimulator()
    
        