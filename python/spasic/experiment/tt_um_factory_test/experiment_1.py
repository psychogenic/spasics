import time

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters


def test_loopback(params:ExperimentParameters, response:ExpResult, num_iterations:int=10):
    print("test_loopback")
    # FAILURES[0..3] NUMITER[0:2] ABORTED
    # 0:4            4:6          6
    response.result = bytearray(7)
    
    # num iterations won't change, set it now
    response.result[4:6] = num_iterations.to_bytes(2, 'little')
    
    tt = params.tt
    # select the project
    tt.shuttle.tt_um_factory_test.enable()
    
    tt.clock_project_PWM(1000) # ensure we have a 1kHz clock rate

    tt.uio_oe_pico.value = 0xff # all outputs from us
    tt.ui_in.value = 0b0
    tt.uio_in.value = 0


    # reset project
    tt.reset_project(True)
    
    tt.clock_project_once() # tick

    # release from reset
    tt.reset_project(False)
    
    num_failures = 0
    
    
    for it in range(num_iterations):
        print(f"it {it}")
        for i in range(256):
            if not params.keep_running:
                print("Aborted")
                response.result[6] = 1
                return 
            
            tt.uio_in.value = i
            time.sleep_ms(2)
            if tt.uo_out.value != i:
                num_failures += 1
                response.result[0:4] = num_failures.to_bytes(4, 'little')
                
