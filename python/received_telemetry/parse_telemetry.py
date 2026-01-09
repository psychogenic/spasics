'''
Parser for Telemetry CSVs collected from satellite.

You may just run:

  python received_telemetry/parse_telemetry.py /tmp/spasic_telemetry_data.csv

from the spasics/python directory.

Interpretation of experiment specific data happens in the 
report_interpreter.py file, located in this module.

@author: Pat Deegan
@copyright: Copyright (C) 2026 Pat Deegan, https://psychogenic.com
'''


import csv
from i2c_client_test import packetdump 
import argparse
from spasic.cnc.response.response import *
from received_telemetry.report_interpreter import StatusResultParserMap, ResultParserMap
class ReportInterpreter:
    
    @classmethod
    def parseResult(cls, exp_id:int, results_bytes:bytearray):
        if exp_id in ResultParserMap:
            try:
                return ResultParserMap[exp_id](results_bytes)
            except Exception as e:
                return f'{results_bytes} (RESULT PARSER FAIL {e})'
        
        return results_bytes

    @classmethod
    def parseStatus(cls, exp_id:int, results_bytes:bytearray):
        
        if exp_id in StatusResultParserMap:
            try:
                return StatusResultParserMap[exp_id](results_bytes)
            except Exception as e:
                return f'{results_bytes} (STATUS PARSER FAIL {e})'
        
        return cls.parseResult(exp_id, results_bytes)


class ResponseOutput:
    def __init__(self):
        pass 
    
    def handle(self, resp:Response, timestamp:str=None):
        
        if not isinstance(resp, Response):
            if resp is None:
                return 
            raise ValueError(f'Passed "{resp}" which is not a Response')
        
        cname = resp.__class__.__name__
        fname = f'handle_{cname}'
        if not hasattr(self, fname):
            print(f'Do not know how to parse {cname}: {resp}')
            return

        getattr(self, fname)(resp, timestamp)
        
    
class ResponsePrinter(ResponseOutput):
    
    def output(self, msg:str, timestamp:str=None):
        if timestamp is None:
            timestamp = ''
        else:
            timestamp = f'{timestamp}: '
            
        print(f'{timestamp}{msg}')
        
    def handle_ResponseOK(self, _resp:ResponseOK, timestamp:str=None):
        self.output('OK', timestamp)
        
    
    def handle_ResponseOKMessage(self, resp:ResponseOKMessage, timestamp:str=None):
        try:
            self.output(f'OK {resp.message.decode("ascii")}', timestamp)
        except UnicodeDecodeError:
            self.output(f'OK {resp.message}', timestamp)
            
        
    def handle_ResponseError(self, resp:ResponseError, timestamp:str=None):
        self.output('ERROR {resp.code} {resp.message}', timestamp)

    def handle_ResponseExperiment(self, resp:ResponseExperiment, timestamp:str=None):
        result = ReportInterpreter.parseResult(resp.exp_id, resp.result)
        
        if resp.exception_id:
            self.output(f'EXPERIMENT {resp.exp_id} with EXCEPTION {resp.exception_id} completed:{resp.completed} result:{result}', timestamp)
        else:
            self.output(f'EXPERIMENT {resp.exp_id} completed:{resp.completed} result:{result}', timestamp)
            
            

    def handle_ResponseStatus(self, resp:ResponseStatus, timestamp:str=None):
        result = ReportInterpreter.parseStatus(resp.exp_id, resp.result)
        if resp.exception_id:
            self.output(f'STATUS EXP {resp.exp_id} with EXCEPTION {resp.exception_id} running:{resp.running} runtime:{resp.runtime}s result:{result}', timestamp)
        else:
            self.output(f'STATUS EXP {resp.exp_id} running:{resp.running} runtime:{resp.runtime}s result:{result}', timestamp)
        

    def handle_ResponseInfo(self, resp:ResponseStatus, timestamp:str=None):
        t = time.gmtime(resp.synctime)
        synctime = f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        self.output(f'INFO v{resp.v_maj}.{resp.v_min}.{resp.v_patch} synctime {synctime}', timestamp)
        
    
class TelemetryParser:
    
    def __init__(self):
        pass 
    
    def dump(self, csvfile:str):
        
        responseParser = ResponsePrinter()
        with open(csvfile) as f:
            reader = csv.DictReader(f, delimiter=',', quotechar='"')
            expname_colname = None
            payload_colname = None
            timestamp_colname = None
            
            # AllRecievedBytes = []
            for row in reader:
                
                # they keep changing the column names, ugh.  Workaround here...
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
                    # print(f'{row[payload_colname]} -> {bts}')
                except ValueError:
                    #print(f"Could not get bits from {row[payload_colname]}\nSkipping")
                    continue
                
                # AllRecievedBytes.append(bts)
                packetdump.set_simulated_pending([bts])
                while True:
                    parsedvals = packetdump.fetch_pending()
                    if parsedvals is None:
                        break 
                    if not isinstance(parsedvals, list):
                        parsedvals = [parsedvals]
                    
                    if not len(parsedvals):
                        break 
    
                    for resp in parsedvals:
                        if isinstance(resp, Response):
                            responseParser.handle(resp, row[timestamp_colname])
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
    