# SpASICs
----------

Scratch repo for work, thoughts and notes about the spasics project: sending an ASIC to space!


It may be possible for [Tiny Tapeout](https://tinytapeout.com/) to include an experiment module aboard a [pocketQube](https://en.wikipedia.org/wiki/PocketQube) class satellite, so am collecting preliminary work on this here, in the hopes of getting ideas and feedback.

## Basic Requirements

Details on the objectives and requirements are all in the PRD, [SpASICs: ASIC Modular satellite experimentation board requirements](doc/SpASICsRequirements.md).  This is also available as [a PDF](doc/spasics.pdf).

## TODO

In addition to feedback on the PRD itself, the following require further work, feedback and ideas:

   * A means to safely run arbitrary, user-submitted, experiments.  Short version is we can't hang, we can't die, no matter what.  The proposed/sample implementation is [experiment_runner.py](python/experiment_runner.py) 
   
   * A complete API for commands and responses from the base system to our module.  Details on that are in [Experiment Module API](doc/ExperimentModuleAPI.md).
   
   * A means to safely update the system (ideally this would go all the way to the uPython firmware itself but, owing to bw constraints, this may be restricted to everything above that layer).  I would like to see something like a 2-slot OTA system, where we have everything in two places, run from slot A, update to slot B, attempt to run from slot B and revert to slot A on failure otherwise slot B becomes primary... that sort of thing.  TBD in [Firmware Updates](doc/FirmwareUpdates.md).
   
   * A byte-efficient means of patching the system.  Some updates may only be changes to a few lines of code, what is the most effective means of transmitting this data?  Also TBD in [Firmware Updates](doc/FirmwareUpdates.md).
   
   * Implementation code for above, once defined
   
   * More TODOs




