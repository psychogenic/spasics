import time
# from spasic.experiment_runner.experiment import ExperimentResponse

def test_loopback(response, num_iterations:int=10):
    print("in test_loopback")
    from ttboard.demoboard import DemoBoard
    tt = DemoBoard.get()
    print("got tt singleton")
    
    tt.shuttle.tt_um_factory_test.enable()

    print("OK 1")
    tt.uio_oe_pico.value = 0xff # all outputs from us
    tt.ui_in.value = 0b0
    tt.uio_in.value = 0
    print("OK 1")
    tt.rst_n.value = 0
    time.sleep_ms(1)
    tt.rst_n.value = 1
    num_failures = 0
    response.result = bytearray(5)
    response.result[0] = num_iterations
    for _it in range(num_iterations):
        for i in range(256):
            tt.uio_in.value = i
            time.sleep_ms(1)
            if tt.uo_out.value != i:
                num_failures += 1
                response.result[1:] = num_failures.to_bytes(4, 'little')
                
