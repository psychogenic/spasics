SpASIC updates
--------------

Would be nice to have everything perfect prior to launch, but... yeah.  So a reliable means of updating code and data is required.

The [Experiment Module API](ExperimentModuleAPI.md) specifies a *PATCH* command, but just how that might work best must be determined.


The 3 main questions at this point are:


1. How can we most efficiently transmit updates and patches?

2. How can we do this in a way that keeps the system resilient and responsive in all cases?

3. Is all this possible for the entire system (meaning down to micropython itself), or must we limit ourselves to updating only our own code and data?


### OTA

It would be nice to have a safe OTA system that somehow supports multiple *slots*, i.e. a known-stable default and an alternate where patches are applied and changes made.  With such a system:

   * we boot up using the current-default slot
   
   * updates are applied to the alternate slot
   
   * a safe (e.g. watchdog protected) attempt is made to use and verify system stability using the new code base
   
   * on success, the slot roles are switched, where alternate slot is promoted to being the default


### Patching

If changes are minor or it's otherwise more efficient, we should be sending updates as patches rather than entire files.  Determination of the most condensed and reliable means to do so are TBD.

