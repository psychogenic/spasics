'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com

Simple system to convert experiment command schedules (@see doc/ExperimentRequests.ods) to 
a CSV for transmission from ground station to sat.

Steps:
  * fill in ExperimentRequests.ods by setting datetime/deltas for individual commands
  * export that to a CSV
  * use this module to 
     generator = generate('/path/to/reqs.csv')
     # and then
     generator.writeCSV('/path/to/schedule_bytes.csv')
     

'''

from i2c_client_test import packetdump
import csv 
import datetime

class TSPacket:
    def __init__(self, action, ts, packets=None):
        self.action = action
        self.timestamp = ts 
        self.packets = packets 
        
    def __repr__(self):
        return f'<TSPacket {self.action} {self.timestamp}: {self.packets}>'
    
class CSVGenerator:
    
    def __init__(self):
        self.tspackets = [] 
        self.current_pack = None 
        packetdump.extend_packets = False
        
        
    def append(self, row, ts):
        
        if self.current_pack is None:
            self.current_pack = TSPacket(row['action'], ts)
        else:
            if ts == self.current_pack.timestamp:
                self.current_pack.action += f" {row['action']}"
            else:
                self.flush()
                self.current_pack = TSPacket(row['action'], ts)
        
        
    def flush(self):
        if self.current_pack is not None:
            self.current_pack.packets = packetdump.packets()
            
            if len(self.current_pack.packets):
                while len(self.current_pack.packets[-1]) < 8:
                    self.current_pack.packets[-1] += bytearray([0])
                    
            self.tspackets.append(self.current_pack)
        self.current_pack = None
            
    def abort(self, timestamp, row):
        self.append(row, timestamp)
        packetdump.abort()
    def run(self, timestamp, row):
        (expid, args) = self.get_experiment_and_parms(row)
        print(f"Run exp {expid} w args {args}")
        self.append(row, timestamp)
        packetdump.run_experiment_now(expid, args)
                
    def reboot(self, timestamp, row):
        self.append(row, timestamp)
        packetdump.reboot()
        
    def status(self, timestamp, row):
        self.append(row, timestamp)
        packetdump.status()
        
    def result(self, timestamp, row):
        self.append(row, timestamp)
        packetdump.experiment_current_results()
        
    def ping(self, timestamp, row):
        self.append(row, timestamp)
        packetdump.ping()
        
        
    def info(self, timestamp, row):
        self.append(row, timestamp)
        packetdump.info()
        
    def queue(self, timestamp, row):
        (expid, args) = self.get_experiment_and_parms(row)
        self.append(row, timestamp)
        packetdump.experiment_queue(expid, args)
        
    def writeCSV(self, topath:str):
        with open(topath, "w") as f:
            writer = csv.writer(f, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['#timestamp', 'action', 'write (bytes)', 'write (hex)', 'read action'])
            for tspack in self.tspackets:
                writepacks = []
                hexpacks = []
                for p in tspack.packets:
                    if type(p) == bytearray:
                        hexpacks.append(f'0x{p.hex()}')
                    writepacks.append(p)
                        
                if len(writepacks) == 1:
                    writepacks = writepacks[0]
                    hexpacks = hexpacks[0]

                writer.writerow([tspack.timestamp, tspack.action, writepacks, hexpacks])

    def get_experiment_and_parms(self, row):
        bts = None
        expid = None
        if len(row['experiment']):
            try:
                expid = int(row['experiment'])
                print(f"EXPID {expid}")
            except:
                print(f"Invalid experiment {row['experiment']}")
        
        if len(row['param']):
            prm = row['param']
            if prm[0] == 'b' and prm[1] == "'":
                bts = eval(prm)
            elif prm[0] == '0' and prm[1] == 'x':
                bts = bytearray.fromhex(prm[2:])
            else:
                print(f"INVALID PARAM {prm}")
                
        return (expid, bts)
def generate(csvfile:str):
    #expects start datetime,    delta ms,    action,    experiment,    param,    packet datetime
    # with action being one of:
    # Run
    # Abort
    # Reboot
    # Status
    # Result
    # Ping
    # Info
    # Queue
    
    generator = CSVGenerator()
    with open(csvfile) as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        
        lastread = None
        for row in reader:
            if not len(row['packet datetime']):
                continue 
            if not len(row['action']):
                continue 
            
            
            # print(row)
            
            action = row['action'].lower()
            
            if not hasattr(generator, action):
                print(f"Unsupported action {action}")
                continue
            
            dt = datetime.datetime.fromisoformat(row['packet datetime'])
            print(f"Calling ACTION {action} @ {dt}")
            act = getattr(generator, action)
            act(dt, row)
            if lastread is None or (dt - lastread) > datetime.timedelta(seconds = 9):
                generator.flush()
                lastread = dt
        if dt:
            generator.flush()
                
    return generator

                                