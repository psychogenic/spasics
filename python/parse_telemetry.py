import csv
from i2c_client_test import packetdump 
import argparse

class TelemetryParser:
    
    def __init__(self):
        pass 
    
    def dump(self, csvfile:str):
        with open(csvfile) as f:
            reader = csv.DictReader(f, delimiter=',', quotechar='"')
            expname_colname = None
            payload_colname = None
            timestamp_colname = None
            for row in reader:
                if expname_colname is None:
                    for cname in ['experiment name', 'teamname']:
                        if cname in row:
                            expname_colname = cname 
                            
                    if expname_colname is None:
                        raise ValueError('could not determine experiment name column header')
                        
                    for cname in ['payload', 'telemetry']:
                        if cname in row:
                            payload_colname = cname 
                    
                    if payload_colname is None:
                        raise ValueError('could not determine payload column header')
                        
                    for cname in ['UTC', 'timestampDate']:
                        if cname in row:
                            timestamp_colname = cname 
                            
                    if timestamp_colname is None:
                        raise ValueError('could not determine timestamp column header')
                        
                        
                        
                if not len(row[expname_colname]):
                    continue 
                if not len(row[payload_colname]):
                    continue 
                if row[expname_colname] != 'spasic':
                    continue
                
                packetdump.set_simulated_pending([bytes.fromhex(row[payload_colname])])
                
                parsedvals = packetdump.fetch_pending()
                if len(parsedvals):
                    print(f'{row[timestamp_colname]}: {parsedvals}')                        

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
    