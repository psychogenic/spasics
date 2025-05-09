'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import machine 
import time 
import random
import os

SlaveAddress = 0x56
ResponseDelaySeconds = 0.5

from i2c_client_packets import ClientPacketGenerator

class SatelliteSimulator:
    '''
        Talks to spasics satellite board over I2C
        and knows how to craft message and interpret 
        data coming back.
    '''
    #def __init__(self, scl:int=25, sda:int=24, baudrate:int=100000):
    def __init__(self, scl:int=23, sda:int=22, baudrate:int=100000):
        self._i2c = machine.I2C(1, scl=scl, sda=sda, freq=baudrate)
        self._start_time = time.time()
        self._ping_count = 0
        self.packet_gen = ClientPacketGenerator()
        
    def send(self, bts:bytearray):
        '''
            send raw bytes over to device
        '''
        try:
            self._i2c.writeto(SlaveAddress, bts)
        except Exception as e:
            print(e)
        time.sleep(0.01)
        
    def read_block(self):
        '''
            read a block of 16 bytes from device
        '''
        empty = bytearray([0x00] * 16)
        try:
            return self._i2c.readfrom(SlaveAddress, 16)
        except Exception as e:
            print(e)
            return empty
    
    def read_pending(self):
        v = self.fetch_pending()
        if v == 'EMPTY':
            return v 
        
        time.sleep(0.02)
        v2 = self.fetch_pending()
        if v2 == 'EMPTY':
            return v 
        
        if isinstance(v, list):
            if isinstance(v2, list):
                for otherval in v2:
                    v.append(otherval)
            else:
                v.append(v2)
        else:
            return [v, v2]
        
    def _parse_block(self, blk):
        if not len(blk):
            return (None, b'')
        if blk == bytearray([0]*len(blk)):
            return (None, b'')
        if blk[0] == 0x01:
            # system message: 0x01 ...
            if blk[1]:
                # ok message: 0x01 [NON-ZERO] ...
                if blk[1] == 0x01:
                    # 0x01 0x01 : OK
                    return ('OK', blk[4:])
                if blk[1] == 0x02:
                    # 0x01 0x02 b'OK' LEN MSGBYTES[LEN]: OK WITH PAYLOAD
                    msglen = blk[4]
                    msg = blk[5:(5+msglen)]
                    return ( f'OK: {msg}', blk[5+msglen:] )
            else:
                # error message
                # 0x01 0x00 ERRCODE LEN MSG[LEN]
                errcode = blk[2]
                errlen = blk[3]
                if errlen:
                    errmsg = blk[4:(4+errlen)]
                else:
                    errmsg = ''
                 
                return ( f'ERROR [{errcode}] {errmsg}', blk[(4+errlen):] )
        
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
            return ( f'Status running:{running} exp {expid} {exstr} {runtime}s: {res}', b'')
        
            
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
                
                
            return ( f'EXPERIMENT {expid}: {end_status} {resmsg}', blk[(5+reslen):] )
            
        elif blk[0] == ord('F'):
            val = 0
            if len(blk) >= 7:
                val = int.from_bytes(blk[3:7], 'little')
            if blk[1:3] == b'SZ':
                # size response
                return (f'FILE size: {val}', blk[7:])
            elif blk[1:3] == b'CS':
                # checksum
                return (f'FILE checksum: {hex(val)}', blk[7:])
            elif blk[1] == ord('D'):
                return (f'FILES LS: {blk[2:]}', b'')
            else:
                return (f'FILE UNKNOWN resp ({blk[1]}): {blk}', b'')
        else:
            return (f"Unknown response: {blk}", b'')
        
        
    def fetch_pending(self):
        '''
            read blocks of 16 bytes until you hit 
            and "empty" response (all 0xff)
            and interpret the data
        '''
        empty = bytearray([0x00]*16)
        
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
            
            
            (parsed_resp, left_overs) = self._parse_block(blk)
            rcvd.append(parsed_resp)
            while left_overs and len(left_overs):
                (parsed_resp, left_overs) = self._parse_block(left_overs)
                if parsed_resp is not None:
                    rcvd.append(parsed_resp)
                
            
            time.sleep_ms(35)
                
        
    def abort(self):
        # b'A'
        print("Requesting experiment abort")
        self.send(self.packet_gen.abort())
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
        
    def time_sync(self):
        # 'T' and 4 bytes of time
        t_now = time.time() - self._start_time
        print(f"Sending time sync {t_now}")
        self.send(self.packet_gen.time_sync(t_now))
        
    def status(self):
        # b'S'
        print("Requesting status")
        self.send(self.packet_gen.status())
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def ping(self):
        # 'P' and payload byte to get back in pong
        self._ping_count += 1
        print(f"Sending ping {self._ping_count}")
        self.send(self.packet_gen.ping(self._ping_count))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def reboot(self, safe_mode:bool=False):
        # 'R' and one byte (safemode, unimplemented)
        print(f"Sending reboot command")
        self.send(self.packet_gen.reboot(safe_mode))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def run_experiment_now(self, experiment_id:int, args:bytearray=None):
        # 'E' EXPID[2]
        print(f"Requesting run of experiment {experiment_id}")
        self.send(self.packet_gen.run_experiment_now(experiment_id, args))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    
    def send_all(self, packets):
        print("Send all", end='')
        for p in packets:
            self.send(p)
            print('.', end='')
            time.sleep(0.040) # give a sec to process
        print()
    def check_file(self, filepath:str):
        print(f"Sending req for size/checksum for {filepath}")
        varid = 1 # could be anything
        packets = self.packet_gen.setvar_list(varid, filepath) # packets to set the filename variable
        
        print("Doing setup...")
        self.send_all(packets)
        time.sleep(ResponseDelaySeconds)
        print(self.read_pending())
        

        self.send(self.packet_gen.filesize(varid))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        self.send(self.packet_gen.checksum(varid))
        print("Getting checksum... give it a sec")
        time.sleep(ResponseDelaySeconds*4)
        print(f'Response: {self.read_pending()}')
        
    def check_file_local(self, filepath:str):
        
        sz = os.stat(filepath)[6]
        
        f = open(filepath, 'rb')
        
        csum = 0
        v = f.read(4)
        while len(v):
            nval = int.from_bytes(v, 'little')
            csum = csum ^ nval
            v = f.read(4)
            
        f.close()
            
        print(f'Local file {filepath}:\n size: {sz}\n checksum: {hex(csum)}')
        
        
    def mkdir(self, dirpath:str):
        print(f"Sending req to make dir {dirpath}")
        varid = 2 # could be anything
        packets = self.packet_gen.setvar_list(varid, dirpath) # packets to set the filename variable
        packets.append(self.packet_gen.mkdir(varid))
        
        self.send_all(packets)
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def lsdir(self, dirpath:str):
        print(f"Sending ls on dir {dirpath}")
        varid = 1
        self.send_all(self.packet_gen.setvar_list(varid, dirpath))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        self.send(self.packet_gen.lsdir(varid))
        time.sleep(ResponseDelaySeconds * 2)
        print(f'Response: {self.read_pending()}')
        
        
        
        
    def file_delete(self, fpath:str):
        srcid = 1
        print(f"Delete {fpath}.  Setting up...")
        self.send_all(self.packet_gen.setvar_list(srcid, fpath))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        self.packet_gen.file_unlink(srcid)
        
    def file_move(self, srcpath:str, destpath:str):
        srcid = 1
        destid = 2
        
        print(f"Move {srcpath} to {destpath}.  Setting up src")
        self.send_all(self.packet_gen.setvar_list(srcid, srcpath))
        
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
        print("Setting up dest")
        self.send_all(self.packet_gen.setvar_list(destid, destpath))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        print("Issuing mv")
        self.send(self.packet_gen.file_move(srcid, destid))
        time.sleep(ResponseDelaySeconds)
        print(f'Response: {self.read_pending()}')
        
    def upload_file(self, srcfile:str, destpath:str, swap_name:str='/mytmp.txt'):
        
        
        infile = open(srcfile, 'rb')
        
        swapid = 1
        destid = 2
        
        # setup our swap file name 
        # and our destination file name
        packets = self.packet_gen.setvar_list(swapid, swap_name)
        packets.extend(self.packet_gen.setvar_list(destid, destpath))
        
        # open the swap file for writes
        packets.append(self.packet_gen.open_write(swapid))
        
        # get all the data from input file (on this MCU)
        # and create write packets, shoot those out as we go
        # to not eat up a bunch of mem
        bts = infile.read(16*6)
        while len(bts):
            new_packets = self.packet_gen.file_write_list(bts)
            print(f'New packets:\n{new_packets}')
            packets.extend(new_packets)
            
            self.send_all(packets)
            packets = []
            
            bts = infile.read(16*6)
            
        # close the file we just wrote... should check that it's
        # size/checksum match but meh
        packets.append(self.packet_gen.file_close())
        
        # move the swap file to the destination file
        packets.append(self.packet_gen.file_move(swapid, destid))
        self.send_all(packets)
        time.sleep(ResponseDelaySeconds)
        print(f"File uploaded to {destpath}.  Getting any pending data")
        print(self.read_pending())
        
        print(f"Issuing request for size and checksum now")
        self.send(self.packet_gen.filesize(destid))
        self.send(self.packet_gen.checksum(destid))
        
        print(f"Gimme a sec")
        time.sleep(ResponseDelaySeconds * 5)
        print(self.fetch_pending())
        
        
        
        

        
        
        
        
        
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
RebootCount = 0
def stressTest():
    global StressCount
    global RebootCount
    
    
    enableReboots = True
    
    
    StressCount = 0
    RebootCount = 0
    runningForeverLoop = False
    while True:
        StressCount += 1
        print(f"Loop {StressCount}")
        if runningForeverLoop:
            runningForeverLoop = False
            print("Aborting forever loop")
            sim.abort()
        else:
            if random.randint(0, 100) > 60:
                runningForeverLoop = True 
                print("Starting forever loop")
                sim.run_experiment_now(3)
            
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
        if enableReboots and random.randint(0, 100) > 90:
            RebootCount += 1
            print(f"*** Rebooting {RebootCount} ***")
            
            sim.reboot()
            time.sleep(12)
            
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
        
sim = SatelliteSimulator()
    