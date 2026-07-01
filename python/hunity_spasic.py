
import asyncio
from hunity_cli import climain
from hunity_api import ExperimentData, CommandInterpreter, ModuleCommand
from datetime import datetime, timezone, timedelta
from received_telemetry.parse_telemetry import ResponsePrinter

from i2c_client_test import packetdump 

from spasic.cnc.response.response import *
ResponseParser = ResponsePrinter()

from dataclasses import dataclass

@dataclass
class TTCommand:
    raw: str 
    command: str
    payload: bytes

    def __repr__(self) -> str:
        return (
            f"TTCommand(command={self.command:<10}, "
            f"payload={self.payload.hex()})"
        )
  
class TTCommandInterpreter(CommandInterpreter):
    
    def __init__(self):
        super().__init__()
    
    
    def process(self, cmd_str:bytes):
        raw_command = bytearray.fromhex(cmd_str)
        raw_command.reverse()
        typebyte = raw_command[0]
        payload = raw_command[1:]
        command_map = {
            
            ord('A'): 'ABORT',
            ord('E'): 'Run',
            ord('E') + ord('I'): 'Exp Result',
            ord('E') + ord('A'): 'Exp Arg',
            ord('E') + ord('Q'): 'Exp Queue',
            
            ord('F') + ord('C'): 'File Close',
            ord('F') + ord('R'): 'File Read',
            ord('F') + ord('W'): 'File Write',
            ord('I'): 'Info',
            ord('P'): 'Ping',
            ord('R'): 'Reboot',
            ord('S'): 'Status',
            ord('T'): 'Time Sync',
            ord('V'): 'Var Get',
            ord('V') + ord('S'): 'Var Set',
            ord('V') + ord('A'): 'Var Append',
            
        }
        
        file_subcommands_map = {
            ord('S'): 'File read size',
            ord('Z'): 'File read checksum',
            ord('O'): 'File read/write',
            ord('D'): 'Create Dir',
            ord('U'): 'File unlink',
            ord('M'): 'File move'
            
        }
        
        if typebyte in command_map:
            return TTCommand(raw = raw_command,command = command_map[typebyte], payload=payload)
        
        if typebyte == ord('F'):
            # filesystem command
            # b'FS' VARID -- read size
            # b'FZ' VARID -- read checksum
            # b'FO' VARID 'R'|'W' -- open for read or write
            # b'FD' VARID -- make a directory (including parents)
            # b'FU' VARID -- unlink/delete a file
            # b'FM' SRCVARID DESTVARID -- move SRC to DEST
            subtype = payload[0]
            payload = payload[1:]
            if subtype in file_subcommands_map:
                return TTCommand(raw = raw_command,command = file_subcommands_map[subtype], payload=payload)
        
        return TTCommand(raw=raw_command, command='UNKNOWN', payload=payload)
                    
                
class TTExperimentDataWrapper:
    def __init__(self, timestamp:datetime, raw_data:str):
        self.result  = ExperimentData(timestamp = timestamp, raw_data=raw_data)

        try:
            bts = bytes.fromhex(self.result.raw_data)
        except ValueError:
            print(f"Could not get bits from {self.result.raw_data}\nSkipping")
            return 
        
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
                    ResponseParser.handle(resp, self.result.timestamp)
                    
    @property
    def timestamp(self):
        return self.result.timestamp 
        
    @property
    def raw_data(self):
        return self.result.raw_data
                    
                    
def main():
    
    cmdInterpret = TTCommandInterpreter()
    try:
        asyncio.run(climain(exp_data_wrapper_class=TTExperimentDataWrapper, command_interpreter=cmdInterpret))
    except KeyboardInterrupt:
        pass
    
if __name__ == "__main__":
    main()