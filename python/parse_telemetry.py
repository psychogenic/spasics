import csv
from i2c_client_test import packetdump 
import argparse
from spasic.cnc.response.response import *

class TelemetryParser:
    
    def __init__(self):
        pass 
    
    def dump(self, csvfile:str):
        with open(csvfile) as f:
            reader = csv.DictReader(f, delimiter=',', quotechar='"')
            expname_colname = None
            payload_colname = None
            timestamp_colname = None
            
            AllRecievedBytes = []
            for row in reader:
                if payload_colname is None:
                    for cname in ['experiment name', 'teamname']:
                        if cname in row:
                            expname_colname = cname 
                            
                    if expname_colname is None:
                        print('could not determine experiment name column header')
                        
                    for cname in ['payload', 'telemetry', 'I2C_EXPS_STATUS_6']:
                        if cname in row:
                            payload_colname = cname 
                    
                    if payload_colname is None:
                        raise ValueError('could not determine payload column header')
                        
                    for cname in ['UTC', 'timestampDate', 'Timestamp']:
                        if cname in row:
                            timestamp_colname = cname 
                            
                    if timestamp_colname is None:
                        raise ValueError('could not determine timestamp column header')
                        
                
                if expname_colname is not None and row[expname_colname] != 'spasic':
                    continue
                
                if row[payload_colname] is None or not len(row[payload_colname]):
                    continue 
                
                try:
                    bts = bytes.fromhex(row[payload_colname])
                except ValueError:
                    #print(f"Could not get bits from {row[payload_colname]}\nSkipping")
                    continue
                
                # AllRecievedBytes.append(bts)
                packetdump.set_simulated_pending([bts])
                
                while packetdump.have_pending():
                    parsedvals = packetdump.fetch_pending()
                    if not isinstance(parsedvals, list):
                        parsedvals = [parsedvals]
                    for resp in parsedvals:
                        if resp is not None:
                            print(f"{row[timestamp_colname]}:{resp}")
def getArgs():
    parser = argparse.ArgumentParser(
        description="Telemetry parser"
    )
    
    parser.add_argument(
        'inputfile', 
        type=str,
        help='The path to the input file to process'
    )
    
    return parser.parse_args()

if __name__ == '__main__':
    args = getArgs()
    parser = TelemetryParser()
    parser.dump(args.inputfile)
    