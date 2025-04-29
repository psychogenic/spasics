import time

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters


def test_loopback(params:ExperimentParameters, response:ExpResult, num_iterations:int=10):
    print("test_loopback")
    
    # NUMITER ABORTED FAILURES[0..3]
    response.result = bytearray(6)
    tt = params.tt
    # select the project
    tt.shuttle.tt_um_factory_test.enable()
    
    tt.clock_project_PWM(1000) # ensure we have a 1kHz clock rate

    tt.uio_oe_pico.value = 0xff # all outputs from us
    tt.ui_in.value = 0b0
    tt.uio_in.value = 0

    tt.rst_n.value = 0
    time.sleep_ms(1)
    tt.rst_n.value = 1
    num_failures = 0
    
    response.result[0] = num_iterations
    for it in range(num_iterations):
        print(f"it {it}")
        for i in range(256):
            if not params.keep_running:
                print("Aborted")
                response.result[1] = 1
                return 
            
            tt.uio_in.value = i
            time.sleep_ms(2)
            if tt.uo_out.value != i:
                num_failures += 1
                response.result[2:] = num_failures.to_bytes(4, 'little')
                
