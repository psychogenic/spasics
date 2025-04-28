'''
Created on Apr 21, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''

import gc
from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from microcotb.time.value import TimeValue
import microcotb as cocotb
from microcotb.utils import get_sim_time
gc.collect()


# get the detected @cocotb tests into a namespace
# so we can load multiple such modules
cocotb.set_runner_scope(__name__)


NumIterations = 20



@cocotb.test()
async def test_loopback(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1

    # ui_in[0] == 0: Copy bidirectional pins to outputs
    dut.uio_oe_pico.value = 0xff # all outputs from us
    dut.ui_in.value = 0b0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    for _it in range(NumIterations):
        for i in range(256):
            dut.uio_in.value = i
            await ClockCycles(dut.clk, 1)
            assert dut.uo_out.value == i, f"uio value unstable {dut.uio_out.value} != {i}"

    dut._log.info("test_loopback passed")


@cocotb.test(timeout_time=100, timeout_unit='us', expect_fail=True)
@cocotb.parametrize(
    clk_period=[10,125], 
    timer_t=[101, 200])
async def test_timeout(dut, clk_period:int, timer_t:int):
    clock = Clock(dut.clk, clk_period, units="us")
    cocotb.start_soon(clock.start())
    # will timeout before the timer expires, hence expect_fail=True above
    await Timer(timer_t, 'us')
    
@cocotb.test(expect_fail=True)
async def test_should_fail(dut):
    
    dut._log.info("Will fail with msg")

    assert dut.rst_n.value == 0, f"rst_n ({dut.rst_n.value}) == 0"






@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("Testing counter")
    
    for _it in range(NumIterations):
        for i in range(256):
            assert dut.uo_out.value == dut.uio_out.value, f"uo_out != uio_out"
            assert int(dut.uo_out.value) == i, f"uio value not incremented correctly {dut.uio_out.value} != {i}"
            await ClockCycles(dut.clk, 1)
        
    
    dut._log.info("test_counter passed")
    

@cocotb.test(skip=True)
async def test_will_skip(dut):
    dut._log.info("This should not be output!")



@cocotb.test(timeout_time=300, timeout_unit='us')
async def test_edge_triggers(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.uio_oe_pico.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info(f"Testing counter, waiting on rising edge of bit 5 at {get_sim_time('us')}us")
    await RisingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.uo_out.value)}")
    
    dut._log.info(f"Now await falling edge")
    await FallingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.uo_out.value)}")
    
    dut._log.info("test_edge_triggers passed")


def main():
    print("tt_um_fact_test main()")
    import ttboard.cocotb.dut
    
    print("class def")
    class DUT(ttboard.cocotb.dut.DUT):
        def __init__(self):
            super().__init__('FactoryTest')
            self.tt = DemoBoard.get()
            # inputs
            self.add_bit_attribute('some_bit', self.tt.uo_out, 5)
    
    print("getting tt obj")
    tt = DemoBoard.get()
    print(f"Got {tt}")
    print("enable project")
    tt.shuttle.tt_um_factory_test.enable()
    
    if tt.mode != RPMode.ASIC_RP_CONTROL:
        print("Setting mode to ASIC_RP_CONTROL")
        tt.mode = RPMode.ASIC_RP_CONTROL
        
    print("all inputs on bidir")
    tt.uio_oe_pico.value = 0 # all inputs
    
    
    TimeValue.ReBaseStringUnits = True # I like pretty strings
    
    
    print("getting the runner")
    runner = cocotb.get_runner(__name__)
    
    print("dut c'tor")
    dut = DUT()
    dut._log.info(f"enabled factory test project.  Will test with {runner}")
    
    print("run test")
    runner.test(dut)
    print("done")