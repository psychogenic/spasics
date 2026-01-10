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
from spasic.experiment.experiment_list import ExperimentsConfig
from spasic.experiment.experiment_result import exception_id_to_type
class ReportInterpreter:
    
    @classmethod
    def parseResult(cls, exp_id:int, results_bytes:bytearray):
        if exp_id in ResultParserMap:
            try:
                return ResultParserMap[exp_id](results_bytes)
            except Exception as e:
                return f'{results_bytes} (RESULT PARSER FAIL {e})'
        
        return f'0x{results_bytes.hex()}'

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
    
    
    def exception_type_string(self, exception_id:int):
        etype = exception_id_to_type(exception_id)
        if etype is not None:
            return etype.__name__
        return 'n/a'
    
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
    
    def experiment_string(self, experiment_id:int):
        if experiment_id in ExperimentsConfig:
            expname = ExperimentsConfig[experiment_id][0].replace('.loader', '')
            
            return f'{expname} [{experiment_id}]'
        
        return str(experiment_id)
    
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
        self.output(f'ERROR {resp.code} {resp.message}', timestamp)

    def handle_ResponseExperiment(self, resp:ResponseExperiment, timestamp:str=None):
        result = ReportInterpreter.parseResult(resp.exp_id, resp.result)
        
        if resp.exception_id:
            self.output(f'EXPERIMENT {self.experiment_string(resp.exp_id)} with EXCEPTION {self.exception_type_string(resp.exception_id)} completed:{resp.completed} result:{result}', timestamp)
        else:
            self.output(f'EXPERIMENT {self.experiment_string(resp.exp_id)} completed:{resp.completed} result:{result}', timestamp)
            
            

    def handle_ResponseStatus(self, resp:ResponseStatus, timestamp:str=None):
        result = ReportInterpreter.parseStatus(resp.exp_id, resp.result)
        if resp.exception_id:
            self.output(f'STATUS EXP {self.experiment_string(resp.exp_id)} with EXCEPTION {self.exception_type_string(resp.exception_id)} running:{resp.running} runtime:{resp.runtime}s result:{result}', timestamp)
        else:
            self.output(f'STATUS EXP {self.experiment_string(resp.exp_id)} running:{resp.running} runtime:{resp.runtime}s result:{result}', timestamp)
        

    def handle_ResponseInfo(self, resp:ResponseStatus, timestamp:str=None):
        t = time.gmtime(resp.synctime)
        synctime = f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        self.output(f'INFO v{resp.v_maj}.{resp.v_min}.{resp.v_patch} synctime {synctime}', timestamp)
    
    
class CSVRow:
    def __init__(self, packet:bytearray, timestamp:str='', 
                 experiment_id:int=None, 
                 experiment_name:str='', response:Response=None, result:bytearray=None, 
                 completed:bool=None,
                 runtime:int=None, exception:str='', comment:str=''):
        self.response_type = 'N/A'
        
        if response is not None:
            rtype = response.__class__.__name__.replace('Response', '')
            self.response_type = rtype
            
        self.timestamp = timestamp if timestamp is not None else ''
        self.experiment_id = str(experiment_id) if experiment_id is not None else ''
        self.experiment_name = experiment_name
        self.completed = str(completed) if completed is not None else ''
        self.packet = packet 
        self.result = f'0x{result.hex()}' if result is not None else ''
        self.exception = exception
        self.comment = comment
        self.runtime = str(runtime) if runtime is not None else ''
        
    @classmethod
    def headerList(cls):
        return [
            '# timestamp',
            'packet',
            'type',
            'exp id',
            'experiment',
            'exception',
            'runtime',
            'result',
            'comment'
            
            ]
        
    def toList(self):
        return [
                self.timestamp,
                f'0x{self.packet.hex()}',
                self.response_type,
                self.experiment_id,
                self.experiment_name,
                self.exception,
                self.runtime,
                self.result, 
                self.comment
            ]
        

class ResponseCVSOutput(ResponseOutput):
    
    def __init__(self, csv_out_path:str=None):
        self.csv_out = None 
        self.out_count = 0
        if csv_out_path is not None:
            self.csv_out = open(csv_out_path, 'w')
             
    def close(self):
        if self.csv_out:
            self.csv_out.close()
    def experiment_string(self, experiment_id:int):
        if experiment_id in ExperimentsConfig:
            return ExperimentsConfig[experiment_id][0].replace('.loader', '')
        
        return str(experiment_id)
    
    def output(self, row:CSVRow):
        rows = []
        if not self.out_count:
            rows.append( ','.join(row.headerList()) )
        
        rows.append(','.join(row.toList()))
        
        outstr = '\n'.join(rows)
        
        if self.csv_out is not None:
            self.csv_out.write(outstr);
            self.csv_out.write('\n')
        else:
            print(outstr)
        
        self.out_count += 1
        
        
        
    def handle_ResponseOK(self, resp:ResponseOK, timestamp:str=None):
        self.output(CSVRow(resp.bytes, timestamp=timestamp, response=resp, comment='OK ACK'))
    
    def handle_ResponseOKMessage(self, resp:ResponseOKMessage, timestamp:str=None):
        try:
            msg = f'OK {resp.message.decode("ascii")}'
        except UnicodeDecodeError:
            msg = f'OK 0x{resp.message.hex()} {resp.message}'
            
        self.output(CSVRow(resp.bytes, timestamp=timestamp, response=resp, comment=msg))
            
        
    def handle_ResponseError(self, resp:ResponseError, timestamp:str=None):
        self.output(CSVRow(resp.bytes, timestamp=timestamp, response=resp, comment=f'ERROR {resp.code} {resp.message}'))
        

    def handle_ResponseExperiment(self, resp:ResponseExperiment, timestamp:str=None):
        result_parsed = ReportInterpreter.parseResult(resp.exp_id, resp.result)
        exception = ''
        if resp.exception_id:
            exception = self.exception_type_string(resp.exception_id)
        r = CSVRow(resp.bytes, timestamp=timestamp, 
                   experiment_id=resp.exp_id,
                   experiment_name=self.experiment_string(resp.exp_id),
                   response=resp, result=resp.result, 
                   completed=resp.completed,
                exception=exception, comment=result_parsed)
        self.output(r)
            

    def handle_ResponseStatus(self, resp:ResponseStatus, timestamp:str=None):
        result_parsed = ReportInterpreter.parseStatus(resp.exp_id, resp.result)
        exception = ''
        if resp.exception_id:
            exception = self.exception_type_string(resp.exception_id)
        r = CSVRow(resp.bytes, response=resp, 
                   timestamp=timestamp, 
                   experiment_id=resp.exp_id,
                   experiment_name=self.experiment_string(resp.exp_id),
                   result=resp.result, 
                   runtime=resp.runtime, 
                   exception=exception, comment=str(result_parsed))
        self.output(r)


    def handle_ResponseInfo(self, resp:ResponseStatus, timestamp:str=None):
        t = time.gmtime(resp.synctime)
        synctime = f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        comment = f'v{resp.v_maj}.{resp.v_min}.{resp.v_patch} synctime {synctime}'
        self.output(CSVRow(resp.bytes, timestamp=timestamp, response=resp, comment=comment))
        
    
class TelemetryParser:
    
    def __init__(self, csv_out_file:str=None):
        self.csv_out_file = csv_out_file
        
    def dump(self, input_csv_file:str):
        
        if self.csv_out_file is not None:
            responseParser = ResponseCVSOutput(self.csv_out_file)
        else:
            responseParser = ResponsePrinter()
            
        responses_parsed = 0
        with open(input_csv_file) as f:
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
                            responses_parsed += 1
                            if self.csv_out_file:
                                print('.', end='')
                    
        
        if self.csv_out_file:
            print()
            print(f'{responses_parsed} responses logged to {self.csv_out_file}')
            responseParser.close()
        else:
            print(f'{responses_parsed} responses parsed.')
            
def getArgs():
    parser = argparse.ArgumentParser(
        description="Telemetry parser"
    )
    
    parser.add_argument(
        'inputfile', 
        type=str,
        help='The path to the input file to process'
    )
    
    parser.add_argument('--outcsv', type=str, required=False,
                        help='Output a CSV file, rather than print')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = getArgs()
    if args.outcsv and args.outcsv == args.inputfile:
        print(f"WHAT?  Don't overwrite {args.inputfile} with output, yo")
    else:
        parser = TelemetryParser(args.outcsv)
        parser.dump(args.inputfile)
    