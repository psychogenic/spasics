# SpASICs Experiment Module API
-------------------------------

As described in the [PRD](SpASICsRequirements.md), the interface to the module is via I2C write and read commands.

We must create an API that allows for management of and updates to the module, as well as performing its primary task of running experiments and collecting data from transmission back to Earth.

Write commands are fixed blobs 8 bytes of data.  Reads are to return 16 bytes.
Responses to commands and experimental results from the module are returned through these read commands, up to 7 of which may be queued for relaying back to us.  That's a whole 112 bytes at a time, so efficiency is something of a consideration.

## TODO

The first item on the list is finalizing a list of supported commands.  From there, formats for such commands and responses are required.


## Formats

The specific formats, payloads, responses etc. for commands and responses are left to be determined once all the supported functionality is actually defined.


## Commands

Commands are orders given to the system, either to perform actions or configure parameters.  These may cause responses to be queued for transmission.


### System Level

Related to base system

#### REBOOT_SAFE

An immediate hard reset of the module, where it reboots in "safe" mode, where it will *only* await for commands.  We may want even this to have a timeout--e.g. reboot to "normal" after 24 hours unless overridden.

#### REBOOT_NORMAL

Hard reset the module immediately, proceeding as normal after restart.

#### SET_SYSTEM_CLOCK

Set the RP2 clock rate in Hz.

#### PATCH

Update or patch a specific piece of code or file.

#### SET_PARAMETER

Update or create a parameter/variable available to and used by the framework.


#### READ_FILE

Return the contents of something on the filesystem.

#### ABORT

Halt any command in progress (e.g. a PATCH or READ_FILE may be in the middle of a data transfer)


#### FLUSH_TX_QUEUE

Clear out all data pending in queue for read responses.



### Experiments

Managing specific design experiments.


#### EXPERIMENT_ENABLE

Enable/disable running of a given experiment.

#### EXPERIMENT_TIMEOUT

Specify the maximum duration of a single run for the experiment.

#### EXPERIMENT_CREATE

Create a slot for a new experiment that may be inserted into the schedule.


#### EXPERIMENT_STATUS

Get status, statistics, other info for a particular experiment.


#### EXPERIMENT_RESULT

Retrieve the last results returned by the given experiment.





### Schedule

Managing scheduled operations.  These may be specific experiment runs or management operations including any of the *System Level* commands.

#### SCHEDULE_ENABLE

Enable or disable the scheduler from running through items in its list.


#### SCHEDULE_LIST

Return the current state and contents of the system schedule.

#### SCHEDULE_CLEAR

Clear out the entire contents of the schedule and reset to base state.


#### SCHEDULE_INSERT

Insert an item (experiment or operation) into the schedule at a specific position.


#### SCHEDULE_REMOVE

Remove an item from the schedule.


#### SCHEDULE_RUN_REPORTS

Get any data queued for transmission by experiments/actions run by the shedule.














