'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import time 
MachineAvailable = False
try:
    import machine 
    MachineAvailable = True
except:
    print("No MACHINE -- only packet constructor available")
    
#import time 
import random
import os

SlaveAddress = 0x56
ResponseDelayMs = 50

from i2c_client_packets import ClientPacketGenerator, ErrorCodes

def error_to_string(error_code:int):
    if error_code in ErrorCodes:
        return ErrorCodes[error_code]
    
    return 'UNKNOWN ERROR'

class ExpResultCache:
    def __init__(self):
        self.id = 0
        self.result = bytearray()
        self.running = 0
        self.exception = 0
        
    def reset(self):
        self.id = 0
        self.result = bytearray()
        self.running = 0
        self.exception = 0
        
    def __str__(self):
        run_str = 'running'
        if not self.running:
            run_str = 'NOT running'
        ex_str = ''
        if self.exception:
            ex_str = f' EXCEPT {self.exception}'
        return f'ID: {self.id} {run_str}{ex_str}: {self.result}'

class SatelliteSimulator:
    '''
        Talks to spasics satellite board over I2C
        and knows how to craft message and interpret 
        data coming back.
    '''
    #def __init__(self, scl:int=25, sda:int=24, baudrate:int=100000):
    def __init__(self, scl:int=23, sda:int=22, baudrate:int=100000, run_quiet:bool=False):
        self._i2c = None
        if baudrate != 0:
            self._i2c = machine.I2C(1, scl=scl, sda=sda, freq=baudrate)
        self._start_time = time.time()
        self._ping_count = 0
        self.packet_gen = ClientPacketGenerator()
        self.exp_result = ExpResultCache()
        self.run_quiet = run_quiet
        
    def output_msg(self, msg, force:bool=False):
        if force or not self.run_quiet:
            print(msg)
        
    
    def ping(self, cnt:int=None):
        '''
            ping -- heartbeat/function check
            @param count: ping count
        ''' 
        # 'P' and payload byte to get back in pong
        if cnt is None:
            self._ping_count += 1
            cnt = self._ping_count
        self.output_msg(f"Sending ping {cnt}")
        self.send(self.packet_gen.ping(cnt))
        self.wait(ResponseDelayMs)
        self.print_response()
        
    def info(self):
        self.send(self.packet_gen.info())
        self.wait(ResponseDelayMs)
        self.print_response()
        
    
    def run_experiment_now(self, experiment_id:int, args:bytearray=None):
        '''
            run_experiment_now -- launch experiment immediately
            @param experiment_id: numerical identifier of experiment
            @param arguments: optional bytearray of arguments for experiment
        '''
        # 'E' EXPID[2]
        self.output_msg(f"Requesting run of experiment {experiment_id}")
        self.exp_result.reset()
        self.send_all(self.packet_gen.run_experiment_now_list(experiment_id, args))
        self.wait(ResponseDelayMs)
        self.print_response()
    
    def status(self):
        '''
            status check of experiment 
            Returns run time, state (completion) and partial results
        '''
        # b'S'
        self.output_msg("Requesting status")
        self.send(self.packet_gen.status())
        self.wait(ResponseDelayMs)
        self.print_response()
        
    def experiment_current_results(self):
        '''
            experiment_current_results 
            Gets immediate report from experiment that is either 
            currently running, or last experiment run.
        '''
        self.output_msg("Requesting experiment current res")
        self.send(self.packet_gen.experiment_result())
        self.wait(ResponseDelayMs)
        self.print_response()
    
    def abort(self):
        '''
            abort -- request an experiment terminate immediately
        '''
        self.output_msg("Requesting experiment abort")
        self.send(self.packet_gen.abort())
        self.wait(ResponseDelayMs)
        self.print_response()
        
        
    def time_sync(self, time_value:int=None):
        '''
            time_sync
            @param time_value: optional integer of current time to set
        '''
        # 'T' and 4 bytes of time
        if time_value is None:
            t_now = int(time.time() - self._start_time)
        else:
            t_now = time_value
        self.output_msg(f"Sending time sync {t_now}")
        self.send(self.packet_gen.time_sync(t_now))
    
    
    def reboot(self, safe_mode:bool=False):
        '''
            reboot 
            Force a system reboot (stops feeding watchdog)
        '''
        # 'R' and one byte (safemode, unimplemented)
        self.output_msg(f"Sending reboot command")
        self.send(self.packet_gen.reboot(safe_mode))
        self.wait(ResponseDelayMs)
        self.print_response()
        
    
    def mkdir(self, dirpath:str):
        '''
            mkdir Create a directory
            @param directory_path: full path of directory
            
            Will create parents as needed.
        ''' 
        self.output_msg(f"Sending req to make dir {dirpath}")
        varid = 2 # could be anything
        packets = self.packet_gen.setvar_list(varid, dirpath) # packets to set the filename variable
        packets.append(self.packet_gen.mkdir(varid))
        
        self.send_all(packets)
        self.wait(ResponseDelayMs)
        self.print_response()
        
    def lsdir(self, dirpath:str):
        '''
            lsdir
            @param directory_path: full path of directory
            will return (possibly multiple responses) with contents 
            of directory
        '''
        self.output_msg(f"Sending ls on dir {dirpath}")
        varid = 1
        self.send_all(self.packet_gen.setvar_list(varid, dirpath))
        self.wait(ResponseDelayMs)
        self.print_response()
        self.send(self.packet_gen.lsdir(varid))
        self.wait(ResponseDelayMs * 2)
        self.print_response()
        
    
    def upload_file(self, srcfile:str, destpath:str, swap_name:str='/mytmp.txt'):
        '''
            upload_file
            @param source: source file path (local)
            @param destination: destination full file path (remote, on module)
            @param swap_name: optional swap file (full path) to use for storage during upload
            
            Utility method that sets up the variables (slots), uploads the file to the 
            temp file and then moves it to its destination on completion.
            
            @note: should be checking the size and checksum prior to rename/move
        '''
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
            # self.output_msg(f'New packets:\n{new_packets}')
            packets.extend(new_packets)
            
            self.send_all(packets)
            packets = []
            
            bts = infile.read(16*6)
            
        # close the file we just wrote... should check that it's
        # size/checksum match but meh
        packets.append(self.packet_gen.file_close())
        
        # TODO: we should interrupt this process and do a file check
        # prior to moving it to destination
        
        # move the swap file to the destination file
        packets.append(self.packet_gen.file_move(swapid, destid))
        self.send_all(packets)
        self.wait(ResponseDelayMs)
        self.output_msg(f"File uploaded to {destpath}.  Getting any pending data")
        self.output_msg(self.read_pending())
        
        self.output_msg(f"Issuing request for size and checksum now")
        self.send(self.packet_gen.filesize(destid))
        self.send(self.packet_gen.checksum(destid))
        
        self.output_msg(f"Gimme a sec")
        self.wait(ResponseDelayMs * 5)
        self.output_msg(self.fetch_pending())
        
    
    def check_file(self, filepath:str):
        '''
            check_file -- utility method to request size and checksum on a file.
           @param filepath: the file in question  
        '''
        self.output_msg(f"Sending req for size/checksum for {filepath}")
        varid = 1 # could be anything
        packets = self.packet_gen.setvar_list(varid, filepath) # packets to set the filename variable
        
        self.output_msg("Doing setup...")
        self.send_all(packets)
        self.wait(ResponseDelayMs)
        self.output_msg(self.read_pending())
        

        self.send(self.packet_gen.filesize(varid))
        self.wait(ResponseDelayMs)
        self.print_response()
        self.send(self.packet_gen.checksum(varid))
        self.output_msg("Getting checksum... give it a sec")
        self.wait(ResponseDelayMs*4)
        self.print_response()
        
    def file_move(self, srcpath:str, destpath:str):
        '''
            file_move -- move/rename a file
            @param source: the (remote) full path of file
            @param destination: the (remote) full path of the new name
            
            Destination directory must exist
        '''
        srcid = 1
        destid = 2
        
        self.output_msg(f"Move {srcpath} to {destpath}.  Setting up src")
        self.send_all(self.packet_gen.setvar_list(srcid, srcpath))
        
        self.wait(ResponseDelayMs)
        self.print_response()
        
        self.output_msg("Setting up dest")
        self.send_all(self.packet_gen.setvar_list(destid, destpath))
        self.wait(ResponseDelayMs)
        self.print_response()
        self.output_msg("Issuing mv")
        self.send(self.packet_gen.file_move(srcid, destid))
        self.wait(ResponseDelayMs)
        self.print_response()
        
    
        
    def file_delete(self, fpath:str):
        '''
            file_delete -- unlink a file
            @param filepath: full path of (remote) file to unlink.
        ''' 
        srcid = 1
        self.output_msg(f"Delete {fpath}.  Setting up...")
        self.send_all(self.packet_gen.setvar_list(srcid, fpath))
        self.wait(ResponseDelayMs)
        self.print_response()
        self.send(self.packet_gen.file_unlink(srcid))
        
    def variable_get(self, v:int):
        self.output_msg(f"Get variable {v}")
        self.send(self.packet_gen.getvar(v))
        self.wait(ResponseDelayMs)
        self.print_response()
        
    def variable_set(self, v:int, value:str):
        self.output_msg(f"Set variable {v} to '{value}'")
        self.send_all(self.packet_gen.setvar_list(v, value))
        self.wait(ResponseDelayMs)
        self.print_response()
        
    
    
    def check_file_local(self, filepath:str):
        '''
            check_file_local
            Check the size and calculate the same checksum as is 
            done on the spasic module.
        '''
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
        
    
        
    def read_pending(self):
        v = self.fetch_pending()
        if v == 'EMPTY':
            return v 
        
        self.wait(20)
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
        
        
        
        
        
        
        
    def wait(self, ms:int):
        time.sleep_ms(int(ms))
        
    def print_response(self):
        self.output_msg(f'Response: {self.read_pending()}')
        
    def monitor_experiment(self, update_freq_ms:int=500):
        
        self.experiment_current_results()
        self.wait(ResponseDelayMs)
        self.read_pending()
        if not self.exp_result.running:
            print(f"Experiment not running {self.exp_result}")
        
        print(f"UPDATE {self.exp_result}")
        rq = self.run_quiet
        self.run_quiet = True
        cur_res = self.exp_result.result
        while self.exp_result.running:
            self.experiment_current_results()
            self.wait(ResponseDelayMs)
            self.read_pending()
            
            if cur_res != self.exp_result.result:
                cur_res = self.exp_result.result
                print(f"UPDATE {self.exp_result}")
                
            time.sleep(update_freq_ms/1000)
            
        self.run_quiet = rq
        print(f"EXP done: {self.exp_result}")
            
        
    def send(self, bts:bytearray):
        '''
            send raw bytes over to device
        '''
        try:
            self._i2c.writeto(SlaveAddress, bts)
        except Exception as e:
            print(e)
            raise e
        self.wait(10)
        
    
    def send_all(self, packets):
        if not self.run_quiet:
            print("Send all", end='')
        for p in packets:
            self.send(p)
            if not self.run_quiet:
                print('.', end='')
            self.wait(40) # give a sec to process
        print()
        
        
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
                 
                return ( f'ERROR "{error_to_string(errcode)}" [{errcode}] {errmsg}', blk[(4+errlen):] )
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
            self.exp_result.running = running 
            self.exp_result.id = expid
            self.exp_result.exception =  exception_id
            self.exp_result.result = res
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
                    end_status = 'RUNNING/INCOMPLETED'
                
            
            self.exp_result.running = False if completed else True 
            self.exp_result.id = expid
            self.exp_result.exception =  except_id
            self.exp_result.result = resmsg
            
            return ( f'EXPERIMENT {expid}: {end_status} {resmsg}', blk[(5+reslen):] )
        
        elif blk[0] == ord('I'):
            # info packet
            payload = blk[1:]
            v_maj = 0
            v_min = 0
            v_patch = 0
            t_now = 0
            t_sync = 0
            if len(payload) < 3+8:
                return (f'INFO -- malformed: {blk}', b'')
        
            v_patch = payload[0]
            v_min = payload[1]
            v_maj = payload[2]
            t_now = int.from_bytes(payload[3:7], 'little')
            t_sync = int.from_bytes(payload[7:11], 'little')
            return (f'INFO v{v_maj}.{v_min}.{v_patch} now:{t_now} sync:{t_sync}', payload[11:])
        
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
            
            try:
                (parsed_resp, left_overs) = self._parse_block(blk)
                rcvd.append(parsed_resp)
            except:
                print(f"Issue parsing block (partial?) {blk}")
                self.wait(35)
                return rcvd
            else:
                while left_overs and len(left_overs):
                        try:
                            (parsed_resp, left_overs) = self._parse_block(left_overs)
                        except:
                            print(f"Issue parsing block (partial?) {left_overs}")
                            self.wait(35)
                            return rcvd
                        if parsed_resp is not None:
                            rcvd.append(parsed_resp)
                
                
            
            self.wait(35)
                
    
        
class PacketConstructor(SatelliteSimulator):
    
    def __init__(self, dumpAscii:bool=True, accumulate_packets:bool=True, prefix:str='PKT: '):
        super().__init__(0, 0, 0) 
        self.dump_ascii = dumpAscii
        self.accumulate_packets = accumulate_packets
        self.prefix = prefix
        self._packets = []
    
    def read_pending(self):
        pass
    
    def packets(self):
        pkts = self._packets 
        self._packets = []
        return pkts
    
    def read_block(self):
        pass 
    def fetch_pending(self):
        pass 
    
    def wait(self, ms:int):
        pass
        
    def print_response(self):
        pass 
    
    
    def send(self, bts:bytearray):
        '''
            send raw bytes over to device
        '''
        if self.accumulate_packets:
            self._packets.append(bts)
                
        hexbts = bytearray(bts)
        if len(hexbts) < 8:
            hexbts.extend(bytearray(8 - len(hexbts)))
        
        hex_str = ','.join(map(lambda x: hex(x) if x>15 else f' {hex(x)}', hexbts))
        if not self.dump_ascii:
            print(f'{self.prefix}{hex_str}')
            return
        spacers = ' '*(50 - len(hex_str))
        mix_str = ' '.join(map(lambda x: f'{x:x}' if x < 0x20 or x > 0x7E else f' {chr(x)}', bts ))
        print(f'{self.prefix}{hex_str}{spacers}{mix_str}')
        
    
    def send_all(self, packets):
        for p in packets:
            self.send(p)
    
        

    def __repr__(self):
        return '<PacketConstructor>'
        
        
        
        
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
        sim.experiment_current_results()
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
        sim.experiment_current_results()
        sim.run_experiment_now(2, random_exp2_params())
        time.sleep(1)
        sim.status()
        time.sleep(4)
        sim.status()
        sim.run_experiment_now(2, random_exp2_params())
        sim.status()
        time.sleep(1)
        sim.status()
        sim.ping()
        sim.experiment_current_results()
        
if MachineAvailable:
    sim = SatelliteSimulator()
    
packetdump = PacketConstructor()
    