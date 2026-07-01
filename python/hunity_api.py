#!/usr/bin/env python3

"""
hunity_api.py

Copyright (C) 2026 Pat Deegan, https://psychogenic.com

WebSocket client for the HUNITY experiment data/command API.
Requires: websockets (pip install websockets)

    async with HunityAPI() as api:
        await api.login("spasic", "pass")
        
        data = await api.getEXPData("spasic", 
                         dt.datetime.now(dt.timezone.utc) - timedelta(hours=12),
                         dt.datetime.now(dt.timezone.utc))
        print(data)
        

"""

SocketDomain="gnd.bme.hu"
PortGroundModel=8280
PortFlightModel=8180

import time
import ssl
import json
import asyncio
from datetime import datetime, timezone, timedelta
import datetime as dt
from dataclasses import dataclass
from typing import Union
import hashlib

import websockets

import logging
OutputVerbose = False
logLevel = logging.WARN
logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logLevel,
)
HunityAPI_User = 'spasic'
HunityAPI_ExpID = 'spasic'
HunityAPI_Password = None
try:
    import hunity_api_auth as hauth
    HunityAPI_User = hauth.User 
    HunityAPI_Password = hauth.Password
    HunityAPI_ExpName = hauth.ExperimentID
except:
    print("No hunity_api_auth found -- will request manual entry")
    


# ---------------------------------------------------------------------------
# Data types returned by the API
# ---------------------------------------------------------------------------
class ModuleCommand:
    def __init__(self):
        pass 
class CommandInterpreter:
    def __init__(self):
        pass 
    
    def process(self, raw_command:str) -> ModuleCommand:
        print("TODO:Override CommandInterpreter to provide implementation")


@dataclass
class CommandWindow:
    id: int
    start: datetime
    end: datetime

    def __repr__(self) -> str:
        return (
            f"CommandWindow(id={self.id}, "
            f"start={self.start.isoformat()}, "
            f"end={self.end.isoformat()})"
        )


@dataclass
class QueuedCommand:
    command_id: int
    timestamp: datetime
    experiment_id: str
    command: str
    windowid: int
    sent: int

    def __repr__(self) -> str:
        return (
            f"QueuedCommand(command_id={self.command_id}, "
            f"command={self.command!r}, "
            f"timestamp={self.timestamp.isoformat()}, "
            f"experiment_id={self.experiment_id!r}, "
            f"windowid={self.windowid}, "
            f"sent={self.sent}) "
        )

@dataclass 
class ExperimentData:
    timestamp: datetime 
    raw_data: str
    
    def __repr__(self) -> str:
        return (
            f"ExperimentData(timestamp={self.timestamp.isoformat()}, "
            f"data={self.raw_data})"
        )

# ---------------------------------------------------------------------------
# Main client class
# ---------------------------------------------------------------------------

class HunityAPI:
    """
    Async HunityAPI client for the experiment command/data API.

    Usage (typical async context)::

        client = HunityAPI()
        await client.open()
        await client.login("spasic", "pass")
        data = await client.getEXPData("spasic", start_dt, end_dt)
        await client.close()

    Or use as an async context manager::

        async with HunityAPI() as client:
            await client.login("spasic", "pass")
            ...
    """


    def __init__(self, port: int = PortGroundModel, 
                    domain: str = SocketDomain, ssl_context=None) -> None:
        self._domain = domain
        self._port = port
        self._uri = f"wss://{domain}:{port}/service"
        self._ws = None  # websockets connection handle
        if ssl_context is None:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        self._ssl_context = ssl_context
    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "HunityAPI":
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def open(self) -> None:
        """Open the WebSocket connection and retain the handle."""
        if self._ws is not None:
            raise RuntimeError("Connection is already open. Call close() first.")
        self._ws = await websockets.connect(self._uri, close_timeout = None,  compression=None, user_agent_header=None, ssl=self._ssl_context)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    # ------------------------------------------------------------------
    # Private: timestamp helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_unix(ts: Union[int, datetime]) -> int:
        """
        Convert a datetime (assumed UTC if naive) to a Unix epoch int32.
        Integers are passed through unchanged.
        Raises ValueError if the result overflows int32.
        """
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                # Treat naive datetime as UTC
                epoch = int(ts.replace(tzinfo=timezone.utc).timestamp())
            else:
                epoch = int(ts.timestamp())
        elif isinstance(ts, int):
            epoch = ts
        else:
            raise TypeError(f"Expected int or datetime, got {type(ts).__name__}")

        # int32 range: −2 147 483 648 … 2 147 483 647
        if not (-(2**31) <= epoch <= 2**31 - 1):
            raise ValueError(f"Unix timestamp {epoch} overflows int32.")
        return epoch

    @staticmethod
    def _from_unix(epoch: int) -> datetime:
        """Convert a Unix epoch integer to a UTC-aware datetime object."""
        return datetime.fromtimestamp(epoch, tz=timezone.utc)

    # ------------------------------------------------------------------
    # Private: generic command sender
    # ------------------------------------------------------------------
    async def get_response(self) -> str:
        raw = await self._ws.recv()
        
        # annoyingly, the server randomly spits out the {"clients": ... } response
        # flush that
        while '"clients"' in raw:
            print(raw)
            raw = await self._ws.recv()
        
        if OutputVerbose:
            print(f"RESPONSE: {raw}")
        return raw 
        
    async def _send_command(self, command: str, *params) -> dict:
        """
        Format and send a command string over the WebSocket.

        The wire format is:   command(param1, param2, ...)
        Parameters are converted to strings via str(); strings are NOT
        quoted in the wire format (the server handles its own parsing).

        Returns a parsed JSON object (dict or list).
        Raises:
            RuntimeError  – if the connection is not open.
            websockets.exceptions.WebSocketException – on transport errors.
            json.JSONDecodeError – if the response is not valid JSON.
        """
        if self._ws is None:
            raise RuntimeError("WebSocket is not open. Call open() first.")

        param_str = ",".join(str(p) for p in params)
        message = f"{command}({param_str})"

        if OutputVerbose:
            print(f"SENDING COMMAND: {message}")
        await self._ws.send(message)
        time.sleep(0.1)
        raw = await self.get_response()
        
        # they keep adding trailing ',' on lists and objects
        # clean those up so we can parse
        chrs = list(raw)
        i = len(chrs) - 1
        while i > 0:
            if chrs[i] == ',':
                chrs[i] = ' '
            elif chrs[i] in ['}', ']', '\n', '\r', ' ', '\t']:
                pass 
            else:
                break 
            i -= 1
            
        raw = ''.join(chrs)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            print(
                f"Response to '{command}' was not valid JSON: {raw!r}")
            return raw

    # ------------------------------------------------------------------
    # Public API commands
    # ------------------------------------------------------------------

    async def login(self, username: str, password: str) -> bool:
        """
        Authenticate with the server.

        Returns True on success, False otherwise.
        Note: the server returns a plain string (not JSON) for this command.
        """
        if self._ws is None:
            raise RuntimeError("WebSocket is not open. Call open() first.")

        enc_pass = hashlib.sha512(
                    password.encode("UTF-8")
                ).hexdigest()
        message = f"login({username}, {enc_pass})"
        
        login = (   #"{"
                    f'"username" : "{username}", '
                    f'"password" : "{enc_pass}"\n'
                    #"}"
                )   
        
        print(f"SENDING COMMAND: {login}")
        await self._ws.send(login)
        response: str  = await self.get_response()

        success = "spasic" in response.lower()
        if success:
            print(f"login: {response.strip()}")
            while 'logged in' not in response.lower():
                time.sleep(0.25)
                response = await self.get_response()
        else:
            print(f"login failed: {response.strip()}")
        return success

    async def getEXPData(
        self,
        experiment_id: str,
        start: Union[int, datetime] = None,
        end: Union[int, datetime] = None,
        data_wrapper: ExperimentData = None
    ) -> str:
        """
        Retrieve experiment data for the given time window.

        Parameters
        ----------
        experiment_id : str
        start : epoch int or datetime (or None, defaults to "now") – window start (UTC)
        end   : epoch int or datetime or timedelta (or None, defaults to +2 days) – window end   (UTC)

        Returns
        -------
            list of [datetime, data]
        """
        if start is None:
            start = datetime.now()
        if end is None:
            end = timedelta(days=2)
            
        if isinstance(end, timedelta):
            end = start + end
            
        t_start = self._to_unix(start)
        t_end = self._to_unix(end)

        try:
            payload = await self._send_command("getEXPData", experiment_id, t_start, t_end)
        except (json.JSONDecodeError, Exception) as exc:
            print(f"getEXPData error: {exc}")
            raise

        lines: list[list] = []
        try:
            datas: dict = payload.get("datas", {})
            for _exp_id, records in datas.items():
                for record in records:
                    dt = self._from_unix(record["unixtimestamp"])
                    if data_wrapper is not None:
                        lines.append(data_wrapper(timestamp=dt, raw_data=record['data']))
                    else:
                        lines.append([dt, record['data']])
        except Exception as e:
            print(f"Could not get 'datas' from {payload}: {e}")
        return lines

    async def getCMDWindows(
        self,
        start: Union[int, datetime] = None,
        end: Union[int, datetime] = None,
    ) -> list[CommandWindow]:
        """
        Retrieve command windows that fall within the given time range.

        Parameters
        ----------
        start : epoch int or datetime (or None, defaults to "now")
        end   : epoch int or datetime or timedelta (or None, defaults to +2 days)

        Returns
        -------
        list[CommandWindow]
        """
        
        if start is None:
            start = datetime.now()
        if end is None:
            end = timedelta(days=2)
            
        if isinstance(end, timedelta):
            end = start + end
        
        t_start = self._to_unix(start)
        t_end = self._to_unix(end)

        try:
            payload = await self._send_command("getCMDWindows", t_start, t_end)
        except (json.JSONDecodeError, Exception) as exc:
            print(f"getCMDWindows error: {exc}")
            raise

        windows: list[CommandWindow] = []
        for w in payload.get("commandwindows", []):
            cw =  CommandWindow(
                    id=w["id"],
                    start=self._from_unix(w["unixtimestampStart"]),
                    end=self._from_unix(w["unixtimestampStop"]),
                )
            windows.append(cw)
            
        
        return windows

    async def deleteCommand(
        self,
        experiment_id: str,
        command_id: int,
    ) -> int:
        """
        Delete a queued command

        Parameters
        ----------
        experiment_id   : str
        command_id   : int

        Returns
        -------
        int
            Server-assigned command ID on success.
        """
        try:
            payload = await self._send_command(
                "deletecommand",
                experiment_id,
                command_id
            )
        except (json.JSONDecodeError, Exception) as exc:
            print(f"sendCommand error: {exc}")
            raise
        return payload
    async def sendCommand(
        self,
        experiment_id: str,
        command_big_hex: str,
        execute_time: Union[int, datetime],
        cmd_window_id: int,
    ) -> int:
        """
        Transmit a command to be executed at the specified time.

        Parameters
        ----------
        experiment_id   : str
        command_big_hex : str   – hex-encoded command payload
        execute_time    : int or datetime – when to execute (UTC)
        cmd_window_id   : int

        Returns
        -------
        int
            Server-assigned command ID on success.

        Raises
        ------
        RuntimeError if the server returns an error string instead of an int.
        """
        t_exec = self._to_unix(execute_time)

        try:
            payload = await self._send_command(
                "sendCommand",
                experiment_id,
                command_big_hex,
                t_exec,
                cmd_window_id,
            )
        except (json.JSONDecodeError, Exception) as exc:
            print(f"sendCommand error: {exc}")
            raise

        # Server returns an integer on success, an error string otherwise.
        if isinstance(payload, int):
            return payload
        print(f"sendCommand returned an error: {payload}")
        return None

    async def getcmdqueue(
        self,
        experiment_id: str,
        start: Union[int, datetime],
        end: Union[int, datetime],
        windowid: int,
        cmd_interpreter: CommandInterpreter = None
    ) -> list[QueuedCommand]:
        """
        Retrieve the command queue for an experiment within a time window.

        Parameters
        ----------
        experiment_id : str
        start         : int or datetime
        end           : int or datetime
        windowid      : int

        Returns
        -------
        list[QueuedCommand]
        """
        t_start = self._to_unix(start)
        t_end = self._to_unix(end)

        try:
            payload = await self._send_command(
                "getcmdqueue", experiment_id, t_start, t_end, windowid
            )
        except (json.JSONDecodeError, Exception) as exc:
            print(f"getcmdqueue error: {exc}")
            raise

        queue: list[QueuedCommand] = []
        for item in payload.get("commandqueue", []):
            # Key names in the spec have a trailing space ("command_id ") —
            # handle both the clean and the space-padded variants defensively.
            cmd_id = item.get("command_id") or item.get("command_id ")
            exp_id = item.get("experiment_id") or item.get("experiment_id ")
            
            if cmd_interpreter is not None:
                cmd = cmd_interpreter.process(item["command"])
            else:
                cmd = item["command"]
            queue.append(
                QueuedCommand(
                    command_id=int(cmd_id),
                    timestamp=self._from_unix(item["unixtimestamp"]),
                    experiment_id=str(exp_id),
                    command=cmd,
                    windowid=item["windowid"],
                    sent=item["sent"],
                )
            )
        return queue

async def main():
    global HunityAPI_Password, HunityAPI_User
    if HunityAPI_Password is None:
        HunityAPI_Password = input('Enter API password: ')
        
    async with HunityAPI() as api:
        logged_in = await api.login(HunityAPI_User, HunityAPI_Password)
        if not logged_in:
            return
        
        data = await api.getEXPData("spasic", 
                         dt.datetime.now(dt.timezone.utc) - timedelta(hours=12),
                         dt.datetime.now(dt.timezone.utc))
        print(data)
    

if __name__ == '__main__':
    print("Hello")
    asyncio.run(main())