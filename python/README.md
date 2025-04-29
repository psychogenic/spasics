# SpASICs Python Driver

This micropython codebase allows:

  * responding to the satellite as an I2C slave device
  
  * running ASIC design experiments and getting results back as they proceed and once they are done



It implements an API that supports:

  * launching and aborting user experiments
  
  * fetching status information
  
  * ping and reboot
  
## Experiments

If you want to write some code that will be run IN SPACE, check the documentation in the [experiment](spasic/experiment) module.

In short, you fork this repo and add your code (following the guidelines in the doc above) in a submodule under spasic.experiment and make a PR.

### Experiment Development

The test you create should use the [TT micropython SDK](https://github.com/TinyTapeout/tt-micropython-firmware), as you'll have access to a `DemoBoard` object to select your project and exercise it.

So, for the most part, dev can happen on your demo board, assuming you have such and a TT06 chip.

We don't have lots of bandwidth for results, so you'll have access to a blob of 10 bytes that you can fill with any data during the run and with final results at the end of your test.  See the examples for details.

So, the first step is just to get some function with test code running, and then to adapt it to the experiment framework.

## Testing

If you want to test the entire codebase, you'll need two devices:

  * one to play the role of the spasics board; and
  
  * one to play the role of the satellite and bus master.
  
and to wire them up with 3 shared lines: I2C SDA, SCL and a common ground.


### satellite simulator

For the satellite, there is [simulator code](./i2c_client_test.py) that can be installed on any micropython device, such as a Pi Pico, as `main.py` and allows you to use the REPL to talk over I2C to the spasics board. 

This code knows how to craft messages and interpret what comes back and has useful methods, e.g.


  * `sim.run_experiment_now(EXPID)` to launch an experiment
  
  * `sim.abort()` to stop an experiment in progress 
  
  * `sim.status()` to read status (experiment running, current results value, etc)
  
  * `sim.ping()` simple check that spasics is alive 
  
  * `sim.reboot()` ... you can probably guess, and
  
  * `sim.read_pending()` to fetch any pending messages on the spasics, such as results of experiments that have completed.
 
### spasics board

Getting a spasics board running is a bit more involved, as the RP2 micropython does *not* currently support I2C slave implementations.

So I had to go deep into the weeds and code up a micropython C module to get it working with our Python.


You'll therefore need a version of uPython with this module built-in.  I have the uPython branch with the C module here: [https://github.com/psychogenic/micropython/tree/rp2-i2cslave](https://github.com/psychogenic/micropython/tree/rp2-i2cslave)

Get that, checkout the rp2-i2cslave branch (`git checkout rp2-i2cslave`), and then copy:

   * all the contents of the [ttboard module directory](https://github.com/TinyTapeout/tt-micropython-firmware/tree/main/src)
   
   * all the contents of the [microcotb module directory](https://github.com/psychogenic/microcotb/tree/main/src)
   
Into `ports/rp2/modules`.  Then build, which is mostly just go into `ports/rp2` and

```
make submodules
make
```

Then you'll have a `firmware.uf2` in build-somethingsomething that you can install

Finally, copy over the [spasics API modules](https://github.com/psychogenic/spasics/tree/main/python/spasic) and the [shuttles](https://github.com/psychogenic/spasics/tree/main/python/shuttles) directory and [config.ini](https://github.com/psychogenic/spasics/blob/main/python/config.ini) [i2c_server.py](https://github.com/psychogenic/spasics/blob/main/python/i2c_server.py) and [main.py](https://github.com/psychogenic/spasics/blob/main/python/main.py), from here, into the root of the micropython filesystem.

For the spasics board, SDA is GPIO2 and SCL is GPIO3. On TT06 demoboards, GPIO2 is the mux control reset (cRST on the header at the top) and GPIO3 is mux control increment (cINC on same header).  So, if you run this on a demoboard, you'll either want to remove the ASIC or remap the I2C pins to something better (say some bidirs, say uio1 and uio2 bidirs... main thing is that they use I2C1 on the RP2 unless you want to mess in the C module).


  
  