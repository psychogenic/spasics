#!/usr/bin/env python3
"""
hunity_cli.py

Interactive command-line interface to the WebSocket experiment API.
Imports and uses hunity_api.HunityAPI.
(C) 2026 Pat Deegan, https://psychogenic.com 


Supported CLI commands
----------------------
  set <VAR> <VALUE>          – set a variable (exp_id, user, password, port)
  get [VAR]                  – show one or all variable values
  model <GROUND|FLIGHT>      – set the model you connect to
  connect                    – open WebSocket and login
  disconnect                 – close WebSocket connection
  command_windows [NUMDAYS]  – list command windows from now to now+NUMDAYS
  command_queue  <WINDOWID> [NUMDAYS] [START]
                             – list commands for window
  send_commands <WINDOW_ID> <CSVFILE>
                             – read CSV and send each row as a command
  send_command_single <WINDOW_ID> <DEADLINE> <HEX_COMMAND>
                             – send the single command
  delete_command <CMDID>     – delete a previously queued command
  help                       – show this help
  
  
  exit / quit                – leave the CLI
"""
import atexit
import asyncio
import csv
import os
import readline
import struct
import sys
from datetime import datetime, timedelta, timezone
import datetime as dt
from typing import Optional, Union

from hunity_api import HunityAPI, PortGroundModel, PortFlightModel, HunityAPI_ExpName, HunityAPI_User, HunityAPI_Password

# ---------------------------------------------------------------------------
# Tab-completion
# ---------------------------------------------------------------------------

COMMANDS = [
    "set", "get", "connect", "disconnect", "model",
    "command_windows", "command_queue", "send_commands", 
    "command_delete",
    "send_command_single",
    "delete_command",
    "poll", "help", "exit", "quit",
]
VARIABLES = ["exp_id", "user", "password", "port"]


def _completer(text: str, state: int) -> Optional[str]:
    buf = readline.get_line_buffer().lstrip()
    tokens = buf.split()

    # First token: complete command names
    if len(tokens) == 0 or (len(tokens) == 1 and not buf.endswith(" ")):
        options = [c for c in COMMANDS if c.startswith(text)]
    # Second token after "set" or "get": complete variable names
    elif len(tokens) >= 1:
        if tokens[0] in ("set", "get"):
            options = [v for v in VARIABLES if v.startswith(text)]
        elif tokens[0] == "model":
            options = [v for v in ["GROUND", "FLIGHT"] if v.startswith(text.upper())]
        else:
            options = []
    else:
        options = []

    return options[state] if state < len(options) else None


readline.set_completer(_completer)
readline.parse_and_bind("tab: complete")
history_file = os.path.expanduser("~/.hunity_cli")
readline.set_history_length(1000)
atexit.register(readline.write_history_file, history_file)

if os.path.exists(history_file):
    try:
        readline.read_history_file(history_file)
    except OSError:
        pass  # Handle empty or corrupted history files smoothly




# ---------------------------------------------------------------------------
# Hex conversion helper
# ---------------------------------------------------------------------------

def _little_endian_hex_to_big_endian_upper(hex_str: str) -> str:
    """
    Convert a little-endian hex string (with or without 0x prefix) to
    upper-case big-endian hex without prefix.

    Example: "0x0000000000000053"  ->  "5300000000000000"
             "0x000000474e500150"  ->  "5001504e47000000"
    """
    hex_str = hex_str.strip()
    if hex_str.lower().startswith("0x"):
        hex_str = hex_str[2:]

    if len(hex_str) % 2 != 0:
        hex_str = "0" + hex_str  # pad to even length

    # Interpret as a sequence of bytes, then reverse for big-endian
    byte_seq = bytes.fromhex(hex_str)
    return byte_seq[::-1].hex().upper()


# ---------------------------------------------------------------------------
# CLI state
# ---------------------------------------------------------------------------

class CLIState:
    def __init__(self) -> None:
        self.vars: dict[str, str] = {
            "exp_id":   "" if HunityAPI_ExpName is None else HunityAPI_ExpName,  
            "user":     "" if HunityAPI_User is None else HunityAPI_User, 
            "password": "" if HunityAPI_Password is None else HunityAPI_Password, 
            "port":     str(PortGroundModel),
        }
        self.client: Optional[HunityAPI] = None
        self.connected: bool = False
        self._command_windows = {}
        
    @property
    def model(self) -> str:
        if self.vars["port"] == str(PortGroundModel):
            return "ground"
        if self.vars["port"] == str(PortFlightModel):
            return "flight"
        return "n/a"
    @property
    def prompt(self) -> str:
        exp = self.vars["exp_id"]
        if self.connected and exp:
            return f"{exp} ({self.model})> "
        return "> "

    def _require_connected(self) -> bool:
        if not self.connected or self.client is None:
            print("Not connected. Run 'connect' first.")
            return False
        return True
        
    def _to_unix(self, ts: Union[int, datetime, None]) -> Optional[int]:
        """Convert datetime to Unix timestamp (int32 style) or pass through int/None."""
        if ts is None:
            return None
        if isinstance(ts, datetime):
            return int(ts.timestamp())  # Unix timestamp (UTC)
        if isinstance(ts, (int, float)):
            return int(ts)
        raise TypeError(f"Expected int, datetime or None, got {type(ts)}")
    
    def _from_unix(self, ts: Union[int, float, None]) -> Optional[datetime]:
        """Convert Unix timestamp to datetime (UTC)."""
        if ts is None:
            return None
        return datetime.fromtimestamp(ts, tz=dt.timezone.utc)
    

    # ------------------------------------------------------------------
    # Command handlers (all async so they can await client calls)
    # ------------------------------------------------------------------
    async def cmd_deletecommand(self, args: list[str]) -> None:
        if len(args) < 1:
            print("Usage: delete_command <CMDID> [MAXID]")
            return
        
        
        exp_id = self.vars["exp_id"]
        if not exp_id:
            print("exp_id is not set. Use: set exp_id <value>")
            return
            
        try:
            cmd_id = int(args[0])
        except ValueError:
            print(f"Pass an integer command id, not '{args[0]}'")
            return 
            
        if len(args) > 1:
            try:
                max_id = int(args[1])
            except ValueError:
                print(f"Pass an integer command id, not '{args[1]}'")
                return 
        else:
            max_id = cmd_id
        
        for i in range(cmd_id, max_id+1):
            resp = await self.client.deleteCommand(exp_id, i)
            print(resp)
            

            
    async def cmd_setmodel(self, args: list[str]) -> None:
        if len(args) < 1:
            print("Usage: model <GROUND|FLIGHT>")
            return
        
        old_port = str(self.vars["port"])
        model = args[0].lower()
        if model == "ground":
            self.vars["port"] = str(PortGroundModel)
        elif model == "flight":
            self.vars["port"] = str(PortFlightModel)
        else:
            print(f"Valid models are GROUND and FLIGHT, '{model}' unrecognized")
            return 
            
        print(f"Port set to {self.vars['port']}") 
        
        if self.vars["port"] != old_port:
            if self.connected:
                print("Port changed, disconnecting")
                await self.cmd_disconnect([])
                
            
    async def cmd_set(self, args: list[str]) -> None:
        if len(args) < 2:
            print("Usage: set <VAR> <VALUE>")
            print(f"  Variables: {', '.join(VARIABLES)}")
            return
        var, value = args[0], args[1]
        if var not in self.vars:
            print(f"Unknown variable '{var}'. Known: {', '.join(VARIABLES)}")
            return
        if var == "port":
            try:
                int(value)
            except ValueError:
                print(f"Port must be an integer, got: {value!r}")
                return
        self.vars[var] = value
        print(f"  {var} = {value}")

    async def cmd_get(self, args: list[str]) -> None:
        if args:
            var = args[0]
            if var not in self.vars:
                print(f"Unknown variable '{var}'. Known: {', '.join(VARIABLES)}")
                return
            val = self.vars[var]
            display = "***" if var == "password" and val else val or "(not set)"
            print(f"  {var} = {display}")
        else:
            for var, val in self.vars.items():
                display = "***" if var == "password" and val else val or "(not set)"
                print(f"  {var} = {display}")

    async def cmd_connect(self, _args: list[str]) -> None:
        if self.connected:
            print("Already connected. Run 'disconnect' first.")
            return

        missing = [v for v in ("user", "password") if not self.vars[v]]
        if missing:
            print(f"Please set: {', '.join(missing)}")
            return

        port = int(self.vars["port"])
        self.client = HunityAPI(port=port)
        try:
            await asyncio.wait_for(self.client.open(), timeout=5.0)
        except Exception as exc:
            print(f"Connection failed: {exc}")
            self.client = None
            return
            
        try:
            ok = await asyncio.wait_for(self.client.login(self.vars["user"], self.vars["password"]), timeout=3.0)
        except:
            print("Login timeout")
            self.connected = False 
            
        if ok:
            self.connected = True

    async def cmd_poll(self, _args: list[str]) -> None:
        try:
            rsp = await self.client.get_response()
            print(f"RESPONSE: {rsp}")
            return rsp
        except: 
            print("Abort")
            pass 
    async def cmd_disconnect(self, _args: list[str]) -> None:
        if not self.connected or self.client is None:
            print("Not connected.")
            return
        try:
            await asyncio.wait_for(self.client.close(), timeout=3.0)
        except asyncio.TimeoutError:
            print("Close timed out - forcing shutdown")
        self.client = None
        self.connected = False
        print("Disconnected.")
        
    async def cmd_getcmdqueue(self, args: list[str]) -> None:
        if not self._require_connected():
            return
        
        exp_id = self.vars["exp_id"]
        if not exp_id:
            print("exp_id is not set. Use: set exp_id <value>")
            return
        if len(args) < 1:
            print("Error: must pass WINDOWID [NUMDAYS] [STARTTIMESTAMP]")
            return
        try:
            window_id = int(args[0])
        except ValueError:
            print(f"WINDOWID must be a number, got: {args[0]!r}")
            return
            
        try:
            numdays = float(args[1]) if len(args) > 1 else 3.0
        except ValueError:
            print(f"NUMDAYS must be a number, got: {args[1]!r}")
            return
            
        starttime = None 
        if len(args) > 2:
            try:
                starttime = int(args[2])
            except ValueError:
                print(f"STARTTIME must be an integer, got {args[2]}")
        
        if starttime is not None:
            start = self._from_unix(starttime)
        else:
            start = datetime.now(tz=timezone.utc)
            
        
        end = start + timedelta(days=numdays)
        
        try:
            cmd_queue = await self.client.getcmdqueue(exp_id, start, end, window_id)
        except Exception as exc:
            print(f"command_windows error: {exc}")
            return
        
        print(f"{len(cmd_queue)} commands returned")
        for qcmd in cmd_queue:
            print(qcmd)
            
        return cmd_queue
        
    async def cmd_command_windows(self, args: list[str]) -> None:
        if not self._require_connected():
            return

        try:
            numdays = float(args[0]) if args else 1.0
        except ValueError:
            print(f"NUMDAYS must be a number, got: {args[0]!r}")
            return

        now = datetime.now(tz=timezone.utc)
        end = now + timedelta(days=numdays)

        try:
            windows = await self.client.getCMDWindows(now, end)
        except Exception as exc:
            print(f"command_windows error: {exc}")
            return

        if not windows:
            print("No command windows found in that range.")
            return

        # Column widths
        id_w = max(len("ID"), max(len(str(w.id)) for w in windows))
        dt_w = 25  # ISO-8601 datetime
        print(f"  {'ID':<{id_w}}  {'Start':<{dt_w}}  {'End':<{dt_w}}")
        print(f"  {'-'*id_w}  {'-'*dt_w}  {'-'*dt_w}")
        for w in windows:
            self._command_windows[w.id] = w
            print(
                f"  {w.id:<{id_w}}  "
                f"{w.start.isoformat():<{dt_w}}  "
                f"{w.end.isoformat():<{dt_w}}"
            )

    async def cmd_send_single_command(self, args: list[str]) -> None:
        if not self._require_connected():
            return

        exp_id = self.vars["exp_id"]
        if not exp_id:
            print("exp_id is not set. Use: set exp_id <value>")
            return
            
        if len(args) < 3:
            print("Usage: send_single_command <WINDOW_ID> <DEADLINE> <HEX_COMMAND>")
            return
        
        try:
            window_id = int(args[0])
        except ValueError:
            print(f"WINDOW_ID must be an int (not '{args[0]}'")
            return 
            
        
        try:
            execute_time = int(args[1])
        except ValueError:
            print(f"DEADLINE must be an int (not '{args[1]}'")
            return 
            
        if execute_time <= 0:
            if window_id not in self._command_windows:
                print("I don't know this window to be able to convert relative time-- use command_windows to fetch first")
                return 
            
            cw = self._command_windows[window_id]
            execute_time = cw.start + timedelta(seconds = abs(execute_time))
            
            if execute_time > cw.end:
                print("Execute time extends beyond window")            
            
        write_hex = args[2]
        
        try:
            command_hex = _little_endian_hex_to_big_endian_upper(write_hex)
        except ValueError as exc:
            print(f"hex conversion error ({exc})")
            return 
        
               
        cmd_id = await self.client.sendCommand(
                    exp_id, command_hex, execute_time, window_id
                )
                
        return cmd_id

    async def cmd_send_commands(self, args: list[str]) -> None:
        if not self._require_connected():
            return

        if len(args) < 2:
            print("Usage: send_commands <WINDOW_ID> <CSVFILE>")
            return

        try:
            window_id = int(args[0])
        except ValueError:
            print(f"WINDOW_ID must be an integer, got: {args[0]!r}")
            return

        csv_path = args[1]
        if not os.path.isfile(csv_path):
            print(f"File not found: {csv_path!r}")
            return

        exp_id = self.vars["exp_id"]
        if not exp_id:
            print("exp_id is not set. Use: set exp_id <value>")
            return

        now = datetime.now(tz=timezone.utc)
        rows = []

        try:
            with open(csv_path, newline="") as fh:
                reader = csv.reader(fh)
                for lineno, row in enumerate(reader, start=1):
                    # Skip blank lines and comment lines (start with #)
                    if not row or row[0].strip().startswith("#"):
                        continue
                    if len(row) < 4:
                        print(f"  Line {lineno}: skipping — expected 4 columns, got {len(row)}")
                        continue
                    rows.append((lineno, row))
        except OSError as exc:
            print(f"Could not read CSV: {exc}")
            return

        if not rows:
            print("No data rows found in CSV.")
            return

        ok_count = 0
        fail_count = 0

        for lineno, row in rows:
            # Columns: event_id, deadline (seconds offset), address, write_hex
            _event_id = row[0].strip()
            deadline_str = row[1].strip()
            _address = row[2].strip()
            write_hex = row[3].strip()

            try:
                deadline_offset = int(deadline_str)
            except ValueError:
                print(f"  Line {lineno}: bad deadline {deadline_str!r} — skipping")
                fail_count += 1
                continue

            execute_time = now + timedelta(seconds=deadline_offset)

            try:
                command_hex = _little_endian_hex_to_big_endian_upper(write_hex)
            except ValueError as exc:
                print(f"  Line {lineno}: hex conversion error ({exc}) — skipping")
                fail_count += 1
                continue

            try:
                cmd_id = await self.client.sendCommand(
                    exp_id, command_hex, execute_time, window_id
                )
                print(f"  Line {lineno}: sent -> command_id={cmd_id}  hex={command_hex}")
                ok_count += 1
            except Exception as exc:
                print(f"  Line {lineno}: sendCommand failed — {exc}")
                fail_count += 1

        print(f"\n  Done: {ok_count} sent, {fail_count} failed.")

    async def cmd_help(self, _args: list[str]) -> None:
        print(__doc__)

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    async def dispatch(self, line: str) -> bool:
        """
        Parse and execute one input line.
        Returns False if the user wants to exit, True otherwise.
        """
        tokens = line.split()
        if not tokens:
            return True

        cmd, args = tokens[0].lower(), tokens[1:]

        if cmd in ("exit", "quit"):
            return False
            
        cmdMap = {
            "set": self.cmd_set, 
            "get": self.cmd_get,
            "model": self.cmd_setmodel,
            "connect": self.cmd_connect,
            "disconnect": self.cmd_disconnect,
            "command_windows": self.cmd_command_windows,
            "command_queue": self.cmd_getcmdqueue,
            "send_commands": self.cmd_send_commands,
            "send_command_single": self.cmd_send_single_command,
            "delete_command": self.cmd_deletecommand,
            "command_delete": self.cmd_deletecommand,
            "poll": self.cmd_poll,
            "help": self.cmd_help
        }
        
        if cmd in cmdMap:
            c = cmdMap[cmd]
            retVal = await c(args)
        else:
            print(f"Unknown command: {cmd!r}. Type 'help' for a list.")

        if retVal:
            return retVal 
            
        return True


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main() -> None:
    state = CLIState()
    print("HUNITY CLI — type 'help' for commands, 'exit' to quit.")

    while True:
        try:
            line = input(state.prompt).strip()
            if not await state.dispatch(line):
                break
        except (EOFError, KeyboardInterrupt):
            print()  # newline after ^C / ^D
            break
    # Clean up if still connected
    if state.connected and state.client is not None:
        await state.cmd_disconnect([])
        print("Connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass