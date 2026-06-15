# HUNITY websocket CLI

Command line interface for configuring HUNITY experiments.

This program and module allow you to connect to the ground and flight model websocket APIs to query and configure commands for experiment modules interactively, and has TAB-completion and persistent/searchable command history (readline support).

Copyright (C) 2026 Pat Deegan, [psychogenic.com](https://psychogenic.com)
Release under the GPL v3, see the LICENSE file for details.

List of available commands from the online help:

```
HUNITY CLI — type 'help' for commands, 'exit' to quit.
> help

hunity_cli.py

Interactive command-line interface to the WebSocket experiment API.
Imports and uses hunity_api.HunityAPI.


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
```


The required files are:

 * [hunity_api.py](../python/hunity_api.py): the module supporting the API; 
 * [hunity_cli.py](../python/hunity_cli.py): the command line interface script; and
 * optionally a `hunity_api_auth.py` to preload auth creds (see Authentication, below)

## Sample Session

```
$ python python/hunity_cli.py

HUNITY CLI — type 'help' for commands, 'exit' to quit.
>
> connect
{"clients": [{"connectionId": "0x71bc94000fa0", "username": "anonymous_56"},{"connectionId": "0x71bc94037de0", "username": "hodlemil"}]}
{"clients": [{"connectionId": "0x71bc94000fa0", "username": "spasic"},{"connectionId": "0x71bc94037de0", "username": "hodlemil"}]}
login: spasic logged in
spasic (ground)> command_windows 0.25
  ID     Start                      End                      
  -----  -------------------------  -------------------------
  45773  2026-06-15T21:50:00+00:00  2026-06-15T22:00:00+00:00
  45774  2026-06-15T22:00:00+00:00  2026-06-15T22:10:00+00:00
  45775  2026-06-15T22:10:00+00:00  2026-06-15T22:20:00+00:00
  45776  2026-06-15T22:20:00+00:00  2026-06-15T22:30:00+00:00
  45777  2026-06-15T22:30:00+00:00  2026-06-15T22:40:00+00:00
  45778  2026-06-15T22:40:00+00:00  2026-06-15T22:50:00+00:00
  45779  2026-06-15T22:50:00+00:00  2026-06-15T23:00:00+00:00
  45780  2026-06-15T23:00:00+00:00  2026-06-15T23:10:00+00:00
  45781  2026-06-15T23:10:00+00:00  2026-06-15T23:20:00+00:00
  45782  2026-06-15T23:20:00+00:00  2026-06-15T23:30:00+00:00
  45783  2026-06-15T23:30:00+00:00  2026-06-15T23:40:00+00:00
spasic (ground)>
spasic (ground)>
spasic (ground)>
spasic (ground)> command_queue 45777
0 commands returned
spasic (ground)>
spasic (ground)>
spasic (ground)> send_command_single 45777 0 0000000000000053
spasic (ground)> send_command_single 45777 -20 0x007056474e500150
spasic (ground)>
spasic (ground)>
spasic (ground)> command_queue 45777
2 commands returned
QueuedCommand(command_id=100, experiment_id='spasic', 
      command='5300000000000000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:00+00:00)
QueuedCommand(command_id=101, experiment_id='spasic', 
      command='5001504E47567000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:20+00:00)
spasic (ground)>
spasic (ground)>
spasic (ground)> send_command_single 45777 -40 0x007056474e500150
spasic (ground)> command_queue 45777
3 commands returned
QueuedCommand(command_id=100, experiment_id='spasic', 
      command='5300000000000000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:00+00:00)
QueuedCommand(command_id=101, experiment_id='spasic', 
      command='5001504E47567000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:20+00:00)
QueuedCommand(command_id=102, experiment_id='spasic', 
      command='5001504E47567000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:40+00:00)
spasic (ground)>
spasic (ground)>
spasic (ground)> command_delete 102
Deleted successfully
spasic (ground)>
spasic (ground)>
spasic (ground)> command_queue 45777
2 commands returned
QueuedCommand(command_id=100, experiment_id='spasic', 
      command='5300000000000000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:00+00:00)
QueuedCommand(command_id=101, experiment_id='spasic', 
      command='5001504E47567000', windowid=45777, sent=0, 
      timestamp=2026-06-15T22:30:20+00:00)
      
spasic (ground)>
spasic (ground)> disconnect
Close timed out - forcing shutdown
Disconnected.
> 
```

## Authentication

To access your experiment, the connection and API calls need to know the experiment id as well as auth credentials, and port to connect to.

These are available and get/set through the get/set commands:

```
>
> get
  exp_id = spasic
  user = spasic
  password = ***
  port = 8280
>
> model
Usage: model <GROUND|FLIGHT>
> model FLIGHT
Port set to 8180
>
>
> get
  exp_id = spasic
  user = spasic
  password = ***
  port = 8180
> 
```

However, if a `hunity_api_auth.py` module is available, with valid values for:

```
# API creds
User = 'myuser'
Password = 'somePassword'
ExperimentID = 'ourexperiment'
```

Then this will be pre-loaded and setup for you on program start.


## commands

The list of commands available is seen through the `help`.  Commands normally also provide online help when run with no parameters:

```

spasic (ground)> send_commands
Usage: send_commands <WINDOW_ID> <CSVFILE>

spasic (ground)> delete_command
Usage: delete_command <CMDID> [MAXID]

spasic (ground)> set
Usage: set <VAR> <VALUE>
  Variables: exp_id, user, password, port

```




spasic (ground)> send_commands
Usage: send_commands <WINDOW_ID> <CSVFILE>
spasic (ground)> delete_command
Usage: delete_command <CMDID> [MAXID]
spasic (ground)> 


