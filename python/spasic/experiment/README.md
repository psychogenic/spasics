# Design Experiments

Goal: run experiments on ASIC designs... in SPACE!

Constraints and limitations: basically memory/stack size and how much data we can report at a time.


The system allows us to launch experiments and collect data as they run and once they have terminated, as well as providing a mechanism to abort a long running process, but all this requires some collaboration from experiment implementers.

## Implementation

You can do anything you like in your (Python) code, and the system requires that you provide a module with a single function having the signature:

```
def my_experiment(params:ExperimentParameters, response:ExpResult):
	# ...
```

This function should be *light-weight*.  Because micropython doesn't support dynamic import of libraries, all the supported experiment runners must be loaded into memory at start-up, so keep it simple.  More details on this below.

### Runner Parameters

At this time, the `ExperimentParameters` has one attribute you must care about, `keep_running`, and another you probably want, `tt`. There is also an `argument_bytes` parameter for advanced use (see below).

The `keep_running` allows for infinite loops, if your experiment calls for such.  It just needs to keep checking `keep_running` to know when to return.  An example of this is in [forever.py](tt_test_experiment/forever.py), which is a test experiment that will run an infinite loop until we tell it to stop.

Here's an example of what that might look like

```
def run_experiment(params:ExperimentParameters, response:ExpResult):
    print("This experiment will run until you tell it to stop")
    try:
        while params.keep_running:
            # do interesting things...
            
        # we've been told to stop, call it completed.
        response.completed = True
    exception Exception as e:
        response.exception = e
```

The params also have a `tt` attribute, which is an instance of the DemoBoard you may use to actually select your design and do things with it.  An example of this is in the [tt_um_factory_test experiments](tt_um_factory_test/).

The results of the run are reported back using the `ExpResult` parameter.  This object is used to report back state, including completion, exceptions encountered and results.  The attributes of interest are

  * `completed`: boolean that starts of False and that you should set True when done
  
  * `exception`: set it to an exception instance should you encounter one
  
  * `results`: the bytes you want to report back

The results are a blob, a `bytearray` of arbitrary format containing up to 10 bytes of data. The results may, and if possible should, be updated as the experiment progresses, such that we can get see it running, get intermediate results as it's going, and possibly get partial results should we get powered-down mid-experiment.

In that [forever.py](tt_test_experiment/forever.py) example, the code begins by setting `results` to a new 4 byte array

```
        response.result = bytearray(4)
```

Then, as it runs, it just updates the value with a count:


```
        while params.keep_running:
            count += 1
            if count > 0xffffff:
                count = 0
            response.result = count.to_bytes(4, 'little')
```

and this way we can get reports of the current count at any time.

For `exception`, see the [failer.py](tt_test_experiment/failer.py) code.  You just catch exceptions and stick them in the attribute.  We don't have the bandwidth or means to get much info about it, but the system can at least report the *fact* of the exception, and it's type.

### Exceptions

Because of (countless!) issues with stack depth, the experiment runners aren't wrapped in any calling function to trap exceptions.  You are expected to this yourself, and ideally report any back using the `exception` attribute of the response. See [failer.py](tt_test_experiment/failer.py) as an example.



### Module structure

As mentioned, memory is at a premium and we can't do much about it.  If you have anything non-trivial, then you want the loader function to


   * be small
   
   * perform imports of your actual code *within* the function
   
   * optionally handle test run settings through the arg bytes
   
See for example: [factory test loader](tt_um_factory_test/loader.py).

It basically does something like this:


```

def run_experiment(params:ExperimentParameters, response:ExpResult):
    try:
        # import of fat test function here
        import spasic.experiment.tt_um_factory_test.experiment_2 as exp2
        exp2.test_counter(params, response, num_iterations=num_iter)
    except Exception as e:
        response.exception = e 
        print(e)
    else:
        response.completed = True
    return
```

This allows us to pre-import all the loader functions without actually loading every single experiment into memory.


### Experiment arguments

The `ExperimentParameters` has an `argument_bytes` attribute that may be used to configure the experimental run.  What's in here and how it will be interpreted is up to you, and it may be up to 10 bytes of data.


The [factory test loader](tt_um_factory_test/loader.py) example actually uses this to set the number of iterations through the test loop and which of two experiments to run.

If you use this, always handle the case where the argument bytes are their default value (all 0).

Also notice that the imports are done only as needed.

```

# optional argument bytes:
#  0: num iterations
#  1: experiment 1 (0), experiment 2 (non zero)
def run_experiment(params:ExperimentParameters, response:ExpResult):
    try:
        # optional number of iterations through test loop to do
        num_iter = params.argument_bytes[0]
        if num_iter == 0:
            num_iter = 50 # default
            
        # which experiment should we run?
        if params.argument_bytes[1]:
            # counter
            import spasic.experiment.tt_um_factory_test.experiment_2 as exp2
            exp2.test_counter(params, response, num_iterations=num_iter)
        else:
            # loopback
            import spasic.experiment.tt_um_factory_test.experiment_1 as exp1
            exp1.test_loopback(params, response, num_iterations=num_iter)
            
    except Exception as e:
        response.exception = e 
        print(e)
    else:
        response.completed = True
    return
```


