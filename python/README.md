# SpASICs Python Driver

This micropython codebase allows:

  * responding to the satellite as an I2C slave device
  
  * running ASIC design experiments and getting results back as they proceed and once they are done



It implements an API that supports:

  * launching and aborting user experiments
  
  * fetching status information
  
  * ping and reboot
  

There is also a framework in place to allow easy development of experiments to run on the module.  If you're interested in that, see the next section and you can ignore the rest.
  
## Experiment Development

Write some code that will be run IN SPACE!  Can be on your own design on TT06, or someone else's.

I've now created a framework to allow you to develop and test your spASIC experiments on TT demoboards.  It's an easy way to see that it's working and doing what you hope, in a way that integrates seamlessly with the spASIC-specific system on the experiment board.

The full description is on [spasic_experiment_testing](https://github.com/psychogenic/spasic_experiment_testing), short version is to

   1. Fork that [spasic_experiment_testing repository](https://github.com/psychogenic/spasic_experiment_testing)

   2. In your clone, create a package under `spasic.experiment` using `spasic.experiment.tt_um_test` as a guide

   3. Copy all the modules over to the demoboard and run your tests using the ExperimentRunner to ensure all is well

   4. Make a pull-request to merge your experiment prior to launch

## Testing

If you want to test this entire codebase, you'll need two devices:

  * one to play the role of the spasics board; and
  
  * one to play the role of the satellite and bus master.
  
to wire them up with 3 shared lines--I2C SDA, SCL and a common ground--and to get a little deeper into the weeds to have the "spasics board" setup.


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

Then you'll have a `firmware.uf2` in build-somethingsomething that you can install.

If you install this UF2, you'll have the spasics basics and you could simply copy over the [spasics API modules](https://github.com/psychogenic/spasics/tree/main/python/spasic) and the [shuttles](https://github.com/psychogenic/spasics/tree/main/python/shuttles) directory and [config.ini](https://github.com/psychogenic/spasics/blob/main/python/config.ini) [i2c_server.py](https://github.com/psychogenic/spasics/blob/main/python/i2c_server.py) and [main.py](https://github.com/psychogenic/spasics/blob/main/python/main.py), from here, into the root of the micropython filesystem.

However, if you are playing deep enough that you have to install the UF2 repeatedly, this process of copying everything over can quickly get tiresome.  

If you want, you can instead take that base UF2 and automatically have the filesystem filled with all the goodness.  To do this, create a directory that will act as the root of the FS, say `upyfs`.  Then, into that directory copy over all the above, so you have:

```
	upyfs/config.ini
	upyfs/i2c_server.py
	upyfs/main.py
	upyfs/shuttles/
	upyfs/spasic/
```

Now, install [uf2utils](https://pypi.org/project/uf2utils/) using `pip install uf2utils`.  With the `firmware.uf2` and the root directory in hand, you can now run

```
python -m uf2utils.examples.custom_pico \
   --fs_root upyfs/ --upython firmware.uf2 \
   --out /tmp/mybundled-distro.uf2
```

Installing the new `/tmp/mybundled-distro.uf2` rather than just the bare `firmware.uf2` will be a bit slower, but it will include everything that was under your `upyfs`.  Horray.
￼


For the spasics board, SDA is GPIO2 and SCL is GPIO3, by default. On TT06 demoboards, GPIO2 is the mux control reset (cRST on the header at the top) and GPIO3 is mux control increment (cINC on same header).  So, if you run this on a demoboard, you'll either want to remove the ASIC or remap the I2C pins to something better (say some bidirs, say uio1 and uio2 bidirs... main thing is that they use I2C1 on the RP2 unless you want to mess in the C module).


  
  