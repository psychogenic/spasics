# SpASICs Experiment Module API
-------------------------------

As described in the [PRD](SpASICsRequirements.md), the interface to the module is via I2C write and read commands.

We must create an API that allows for management of and updates to the module, as well as performing its primary task of running experiments and collecting data from transmission back to Earth.

Write commands are fixed blobs 8 bytes of data.  Reads are to return 16 bytes.
Responses to commands and experimental results from the module are returned through these read commands, up to 7 of which may be queued for relaying back to us.  That's a whole 112 bytes at a time, so efficiency is something of a consideration.


## Current Implementation

The current system does its best to be mostly stateless: i.e. where it can, operations are transmitted over a single 8-byte write transaction.  This rule is broken in cases where more than 8 bytes need to be transmitted but, even in these instances, there is no required set timing or order on the commands issued.

For example, if I am writing a file, I will need to setup the destination path prior to beginning the write, but so long as power is applied, the transmission of data for the file may be interleaved with other commands like launching experiments or getting status information.

The actual implementation of the protocol mostly happens in the [i2c_server_handlers](../python/i2c_server_handlers.py) module, and is documented here.

In order to verify function during development and to assist in crafting command packets, there is also client side code, found in   [i2c_client_packets](../python/i2c_client_packets.py) and [i2c_client_test](../python/i2c_client_test.py). 


## Crafting command Packets

These client-side modules have been written such that they may be used to interact with a live board over I2C, or simply on a desktop computer, in order to inspect or export the packet contents.

To do so, it's only a matter of importing everything from `i2c_client_test` and using the `packetdump` instance.

Issuing a command will output information, as well as "packet" lines, with the hex bytes as well as any ascii values, to the right.


All multi-byte integer values used are **little-endian**.

```
>>> from i2c_client_test import *
>>>
>>>
>>> packetdump.ping()
Sending ping 1
PKT: 0x50, 0x1,0x50,0x4e,0x47, 0x0, 0x0, 0x0            P 1  P  N  G
>>>
>>> packetdump.ping()
Sending ping 2
PKT: 0x50, 0x2,0x50,0x4e,0x47, 0x0, 0x0, 0x0            P 2  P  N  G
>>>
>>> packetdump.ping(0x88)
Sending ping 136
PKT: 0x50,0x88,0x50,0x4e,0x47, 0x0, 0x0, 0x0            P 88  P  N  G
>>>
>>> packetdump.run_experiment_now(3, b'some args 123')
Requesting run of experiment 3
PKT: 0x86,0x73,0x6f,0x6d,0x65,0x20,0x61,0x72           86  s  o  m  e     a  r
PKT: 0x86,0x67,0x73,0x20,0x31,0x32,0x33, 0x0           86  g  s     1  2  3
PKT: 0x45, 0x3, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            E 3 0
>>>
>>>
>>> # collect the packets, e.g. for export
>>>
>>> packetdump.packets()
[bytearray(b'P\x01PNG\x00\x00\x00'), 
 bytearray(b'P\x02PNG\x00\x00\x00'), 
 bytearray(b'P\x88PNG\x00\x00\x00'), 
 bytearray(b'\x86some ar'), 
 bytearray(b'\x86gs 123\x00'), 
 bytearray(b'E\x03\x00\x00\x00\x00\x00\x00')]
```

I'll use this utility throughout to demonstrate packet contents.


## Available commands

All commands start with at least one command type byte, optionally followed by "sub-command" bytes or payload.  

In the following, hard-coded values will be specified in hex and variable values will just be assigned their `[LENGTH]` with 
`[A..B]` denoting a length between A and B.

### Ping

Simple method of determining life.  The ping expects one counter byte and an optional payload that will be echoed back.

The format is 

```
'P'   CNT  PAYLOAD
0x50  [1]  [0..6]
```
Sample
```
>>> packetdump.ping(0x42)
Sending ping 2
PKT: 0x50,0x42,0x50,0x4e,0x47, 0x0, 0x0, 0x0            P  B  P  N  G
```

Responds with an acknowledgement "pong" packet, containing the original counter byte and payload.



### Run Experiment (Immediate)

Running experiments is why we're up there.

Experiments will all be assigned a numeric ID.  Experiments *may* support arguments (using the next command described).

```
'E'   ID
0x45  [2]
```

Sample
```
packetdump.run_experiment_now(0x33)
Requesting run of experiment 51
PKT: 0x45,0x33, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            E  3 0

```

Responds with OK or an error message.

### Run Experiment Arguments

Because arguments may have more bytes than a single command can handle, these are cummulative and stateful.  Any length of bytes of arguments can in theory be sent over, using multiple of these commands.

Note that these must be sent prior to launching the experiment, and the state of the arguments is cleared on calling run experiment (regardless of success) and on abort.


```
'E'+'A'  ARGS
0x86     [1..7]
```

Here is a sample to launch experiment 0x44 with more arguments than can be handled with a single call.  The final packet is the launch of the experiment itself.



```
>>> packetdump.run_experiment_now(0x44, b'abc123456')
Requesting run of experiment 68
PKT: 0x86,0x61,0x62,0x63,0x31,0x32,0x33,0x34           86  a  b  c  1  2  3  4
PKT: 0x86,0x35,0x36, 0x0, 0x0, 0x0, 0x0, 0x0           86  5  6
PKT: 0x45,0x44, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            E  D 0
```

No response.


### Queue Experiment

Queue an experiment to run.  This is similar to the run now, but allows us to queue multiple experiments, whether something is running now or not.

If no experiment is currently running, the first queued experiment will be launched.  Other than the command byte itself for queueing, the process is identical to run now.

The only caveat is that this queue is non-persistent: if we power cycle or reboot, the queue goes away.

Command

```
'E'+'Q   EXPID
0x49      [2]
```

Here's a sample queue of experiment 1 and experiment two along with some arguments.

The argument setting process is the same as for run now

```
>>> packetdump.experiment_queue(1)
Queueing experiment 1
PKT: 0x96, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           96 1 0
>>>
>>> packetdump.experiment_queue(2, b'123abc')
Queueing experiment 2
PKT: 0x86,0x31,0x32,0x33,0x61,0x62,0x63, 0x0           86  1  2  3  a  b  c
PKT: 0x96, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           96 2 0
>>> 
```

Responds with OK or error if no such experiment is mapped.

### Status

Requesting status will queue a response that includes information on the current (or last) experiment, its run time, its completion or if any exceptions were caught as well as (potentially partial) current results specified by the code.

It is a single byte of actual data:

```
'S'
0x53
```

Sample
```
>>> packetdump.status()
Requesting status
PKT: 0x53, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            S
```

Responds with a status packet.

### Experiment Current Results

At the end of an experiment run, a result packet will be added to the response queue.  For experiments that run for a longer duration, or that require intermediate result reports beyond what `status` can provide, this command will prompt the system to queue a report immediately, with whatever the experiment has set in the result field at the time.


It is a single byte command

```
'E'+'I'
0x8e
```
Sample
```
>>> packetdump.experiment_current_results()
Requesting experiment current res
PKT: 0x8e, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           8e
```

Responds with an experiment report.

### Abort

A long running (or infinite) experiment may be terminated by calling abort.

This is another single byte command.  You guessed it, it's an "A".

```
'A'
0x41
```

Sample

```
>>> packetdump.abort()
Requesting experiment abort
PKT: 0x41, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            A
```

Responds with OK, indicating whether termination was issued.

### Time Sync

The time sync command sets the system time (ish).

It has a payload of a 4-byte integer

```
'T'   TIME
0x54  [4]
```

Sample
```
>>> packetdump.time_sync(0x12345678)
Sending time sync 305419896
PKT: 0x54,0x78,0x56,0x34,0x12, 0x0, 0x0, 0x0            T  x  V  4 12
>>> 
```

No response.

### Reboot

Reboots the system (by starving the watchdog, for a hard hard reset).

```
'R'
0x82
```

Sample

```
Sending reboot command
PKT: 0x52, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            R 0
>>> chr(0x52)
```

Responds with OK.


### Info

Version and time information is return with 


```
'I'
0x49
```

Responds with a Info packet including version, system time and sync time.


## Filesystem Management

Updates and management of file system (checking file sizes and checksums, moving or deleting files) are now supported.

### Variable Slots
In order to support these operations, which potentially require multiple uses of long strings, a system of *variable slots* was introduced.  These will be described below but in short you can set up to 256 variables to strings of any length, giving each a unique numerical ID.

Then, in many operations, rather than passing a filename around for example, the system uses the single byte variable ID previously set up.  These will show up in the examples below.

### Make Directory

To create a directory, you set up a variable with the full path (including all parents from root) and it will create the directory if possible, including all the parents that are missing.

```
'F'   'D'   VARID
0x46  0x44  [1]
```

The command is simple but, in this sample, you'll notice the first three packets do the work of setting up a variable (id #2 in this case) and only the final packet is the command to create the directory:

```
>>> packetdump.mkdir('/path/to/targetdir')
Sending req to make dir /path/to/targetdir
PKT: 0xa9, 0x2,0x2f,0x70,0x61,0x74,0x68,0x2f           a9 2  /  p  a  t  h  /
PKT: 0x97, 0x2,0x74,0x6f,0x2f,0x74,0x61,0x72           97 2  t  o  /  t  a  r
PKT: 0x97, 0x2,0x67,0x65,0x74,0x64,0x69,0x72           97 2  g  e  t  d  i  r
PKT: 0x46,0x44, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0            F  D 2
```

Responds with OK or error.

### List Directory

Get the contents, potentially over multiple queued responses, of a target directory

```
'F'   'L'   VARID
0x46  0x4c   [1]
```

Sample (in this case, variable slot 1 is used)
```
>>> packetdump.lsdir('/spasics')
Sending ls on dir /spasics
PKT: 0xa9, 0x1,0x2f,0x73,0x70,0x61,0x73,0x69           a9 1  /  s  p  a  s  i
PKT: 0x97, 0x1,0x63,0x73, 0x0, 0x0, 0x0, 0x0           97 1  c  s
PKT: 0x46,0x4c, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0            F  L 1
```

Returns one or more File responses or error.


### File Upload

This isn't an actual command, but a utility in the satellite simulator and packet dumper that performs multiple operations:

   * sets up swap space and destination variables
   
   * opens (swap) file for write access
   
   * sends all the contents in write-sized chunks
   
   * closes the file that was opened for write
   
   * move the file over from swap to dest
   
   * requests file size and checksum info for dest


NOTE: In a real use case, it would be much safer to check the size and checksum on the swap file prior to proceeding to the move!

Still, this gives a good idea of the entire process and proves that it is possible to update the firmware (or at least the scripts on the FS) as we go.

```

>>> packetdump.upload_file('mytest.txt', '/path/to/dest.txt')
# set up a swap space variable (1) and destination variable (2)
PKT: 0xa9, 0x1,0x2f,0x6d,0x79,0x74,0x6d,0x70           a9 1  /  m  y  t  m  p
PKT: 0x97, 0x1,0x2e,0x74,0x78,0x74, 0x0, 0x0           97 1  .  t  x  t
PKT: 0xa9, 0x2,0x2f,0x70,0x61,0x74,0x68,0x2f           a9 2  /  p  a  t  h  /
PKT: 0x97, 0x2,0x74,0x6f,0x2f,0x64,0x65,0x73           97 2  t  o  /  d  e  s
PKT: 0x97, 0x2,0x74,0x2e,0x74,0x78,0x74, 0x0           97 2  t  .  t  x  t

# open file 1 (the swap) for write
PKT: 0x46,0x4f, 0x1,0x57, 0x0, 0x0, 0x0, 0x0            F  O 1  W

# send the data bytes in small chunks
PKT: 0x9d,0x54,0x68,0x65,0x73,0x65,0x20,0x61           9d  T  h  e  s  e     a
PKT: 0x9d,0x72,0x65,0x20,0x74,0x68,0x65,0x20           9d  r  e     t  h  e   
PKT: 0x9d,0x63,0x6f,0x6e,0x74,0x65,0x6e,0x74           9d  c  o  n  t  e  n  t
PKT: 0x9d,0x73, 0xa,0x6f,0x66,0x20,0x74,0x68           9d  s a  o  f     t  h
PKT: 0x9d,0x65,0x20,0x66,0x69,0x6c,0x65,0x2e           9d  e     f  i  l  e  .
PKT: 0x9d, 0xa, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           9d a

# close the file that was opened
PKT: 0x89, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           89

# move the swap file (1) to destination (2)
PKT: 0x46,0x4d, 0x1, 0x2, 0x0, 0x0, 0x0, 0x0            F  M 1 2


File uploaded to /path/to/dest.txt.  Getting any pending data

Issuing request for size and checksum now
PKT: 0x46,0x53, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0            F  S 2
PKT: 0x46,0x5a, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0            F  Z 2

```

### Checking files

Two commands assist with checking the contents of files without having to read the entire thing:

  * size and
  
  * checksum

Both need a variable slot setup prior to use.

```
Size
'F'   'S'   VARID
0x46  0x53  [1]

Checksum
'F'   'Z'   VARID
0x46  0x5a  [1]

```

If you do these both at once, you can avoid setting up the variable slot twice.

Sample
```
>>> packetdump.check_file('/main.py')
Sending req for size/checksum for /main.py
Doing setup...
PKT: 0xa9, 0x1,0x2f,0x6d,0x61,0x69,0x6e,0x2e           a9 1  /  m  a  i  n  .
PKT: 0x97, 0x1,0x70,0x79, 0x0, 0x0, 0x0, 0x0           97 1  p  y
None
PKT: 0x46,0x53, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0            F  S 1
PKT: 0x46,0x5a, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0            F  Z 1
```


In this case, both a File size and File checksum response.

### File Move

Moving, or renaming, a file.  After setting up the two variable slots, it's simply



```
Size
'F'   'M'   SRCID  DESTID
0x46  0x4d   [1]    [1]
```

Sample, moving *a.txt* to *b.py*:
```
>>> packetdump.file_move('a.txt', 'b.py')
Move a.txt to b.py.  Setting up src
PKT: 0xa9, 0x1,0x61,0x2e,0x74,0x78,0x74, 0x0           a9 1  a  .  t  x  t
Setting up dest
PKT: 0xa9, 0x2,0x62,0x2e,0x70,0x79, 0x0, 0x0           a9 2  b  .  p  y
Issuing mv
PKT: 0x46,0x4d, 0x1, 0x2, 0x0, 0x0, 0x0, 0x0            F  M 1 2
>>> 
```

### File Delete

Unlinking a file is possible (use with caution of course).


```
'F'   'U'   VARID
0x46  0x55   [1]
```

Sample

```
>>> packetdump.file_delete('/path/file.txt')
Delete /path/file.txt...
PKT: 0xa9, 0x1,0x2f,0x70,0x61,0x74,0x68,0x2f           a9 1  /  p  a  t  h  /
PKT: 0x97, 0x1,0x66,0x69,0x6c,0x65,0x2e,0x74           97 1  f  i  l  e  .  t
PKT: 0x97, 0x1,0x78,0x74, 0x0, 0x0, 0x0, 0x0           97 1  x  t
# the actual delete operation on var 1
PKT: 0x46,0x55, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0            F  U 1
>>> 
```


## File open

Files may be opened for read or writes.  For the open, you need to setup a variable slot and then call the right open command.  While it's open, you can issue multiple read/writes as appropriate.


```
'F'   'O'    VARID  'R'|'W'
0x46  0x4f   [1]      [1] (either 0x52 or 0x57) 
```


Sample, sending b'W' for a write, to a previously setup variable in slot 3
```
# open file using var 3 for write
PKT: 0x46,0x4f, 0x3,0x57, 0x0, 0x0, 0x0, 0x0            F  O 3  W
```


## Write to Open File


Once a file has been opened, writing to it can be done in 7-byte chunks with:

```
'F'+'W'  CONTENTS
0x9D      [1..7]

```

Sample
```
# open file from slot 1 for write
PKT: 0x46,0x4f, 0x1,0x57, 0x0, 0x0, 0x0, 0x0            F  O 1  W

# send the data bytes in small chunks
PKT: 0x9d,0x54,0x68,0x65,0x73,0x65,0x20,0x61           9d  T  h  e  s  e     a
PKT: 0x9d,0x72,0x65,0x20,0x74,0x68,0x65,0x20           9d  r  e     t  h  e   
PKT: 0x9d,0x63,0x6f,0x6e,0x74,0x65,0x6e,0x74           9d  c  o  n  t  e  n  t
PKT: 0x9d,0x73, 0xa,0x6f,0x66,0x20,0x74,0x68           9d  s a  o  f     t  h
PKT: 0x9d,0x65,0x20,0x66,0x69,0x6c,0x65,0x2e           9d  e     f  i  l  e  .
PKT: 0x9d, 0xa, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           9d a

# close the file that was opened
PKT: 0x89, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0           89
```



## Close File

It's nice to close the files you've opened.

The command is a single byte
```
'F'+'W'
0x89
```

For a sample, see just above.


## Variable store

As demonstrated above, there are variable slots that may be used to store long strings that get used in some commands.

### Setting variables

Setting actually involves two commands, one to initialize a slot to a value, and another to append to an existing value.


```
Set/Init
'V'+'S'   VARID  CONTENTS
0xA9       [1]   [1..6]

Append
'V'+'A'   VARID  CONTENTS
0x97
```

Sample using `variable_set()` to handle both the init and all the required appends:

```
>>> packetdump.variable_set(0x8, '/some/very/long/string/path/file.py')
Set variable 8 to '/some/very/long/string/path/file.py'
PKT: 0xa9, 0x8,0x2f,0x73,0x6f,0x6d,0x65,0x2f           a9 8  /  s  o  m  e  /
PKT: 0x97, 0x8,0x76,0x65,0x72,0x79,0x2f,0x6c           97 8  v  e  r  y  /  l
PKT: 0x97, 0x8,0x6f,0x6e,0x67,0x2f,0x73,0x74           97 8  o  n  g  /  s  t
PKT: 0x97, 0x8,0x72,0x69,0x6e,0x67,0x2f,0x70           97 8  r  i  n  g  /  p
PKT: 0x97, 0x8,0x61,0x74,0x68,0x2f,0x66,0x69           97 8  a  t  h  /  f  i
PKT: 0x97, 0x8,0x6c,0x65,0x2e,0x70,0x79, 0x0           97 8  l  e  .  p  y
```

### Getting variables

Getting the contents of a variable slot is simply


```
'V'   VARID
0x56   [1]

```

E.g. 

```
>>> packetdump.variable_get(0x8)
Get variable 8
PKT: 0x56, 0x8, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0            V 8
```

## Responses

The responses are all parsed and understood in [i2c_client_test](../python/i2c_client_test.py), so their format is left as an exercise to the reader, for the moment ;-)


Have fun,
Pat Deegan
