'''
SPDX-FileCopyrightText: Copyright (C) 2025 Darryl L. Miles <darryl.miles@darrylmiles.org>
SPDX-License-Identifier: Apache2.0

Example test usages:

from spasic.experiment_runner import ExperimentRunner
runner = ExperimentRunner()
LAUNCH_ID = 17
runner.launch(LAUNCH_ID)
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x01\x01\x01\x00\x01\x00\x00') # 1 * 1 = 1
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x02\x01\x02\x00\x01\x00\x00') # 2 * 1 = 2
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x02\x02\x04\x00\x01\x00\x00') # 2 * 2 = 4
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x7f\x02\xfe\x00\x01\x00\x00') # 127 * 2 = 254
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x7f\x03\x7d\x01\x01\x00\x00') # 127 * 3 = 381
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x7f\x03\x7d\x01\x03\x00\x00') # 127 * 3 = 381 (3 iterations)
runner.launch(LAUNCH_ID, b'\x00\x08\x00\x7f\x03\x7d\x01\xe8\x03\x00') # 127 * 3 = 381 (1000 iterations)

'''
import time
import machine
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters


def wait(n: int = 1) -> None:
    time.sleep_ms(n)
    pass


def addr_set(tt, uio_in: int, bf: bool = None, skip_commit: bool = False) -> int:
    if bf is None:
        uio_in ^= 0x1 # invert
    elif bf:
        uio_in |= 0x1 # A1
    else:
        uio_in &= ~0x1 # A0
    if not skip_commit:
        tt.uio_in.value = uio_in
        wait() # settle delay
    return uio_in


def clock_on(tt) -> None:
    tt.pins.pin_rp_projclk.on()


def clock_off(tt) -> None:
    tt.pins.pin_rp_projclk.off()


def clock_cycle(tt, count: int = 1) -> None:
    while count > 0:
        if tt.pins.pin_rp_projclk():
            clock_off(tt)
            wait()
        clock_on(tt)
        wait()
        count -= 1


# Response structure
def populate_response(ba: bytearray, count: int, r: int, c: int, good_count: int, last: int) -> None:
    ba[0:2] = r.to_bytes(2, 'little')
    tmp = (c & 0xf0f0) | (last & 0x0f)
    # c BITS expected only [13:12] [5:4] are valid from EDIV0/EOVER
    if count & 0xff0000 == good_count & 0xff0000:
        tmp |= 0x0400 # MSB is valid
    ba[2:4] = tmp.to_bytes(2, 'little')
    ba[4:8] = count.to_bytes(4, 'little')
    ba[8:10] = good_count.to_bytes(2, 'little') # LSBs
    #print(f'RESULT = r={r:04x} c_and_flags={tmp:04x} count={count:06x} good_count={good_count:06x}')
    #print(f'RESULT = {ba}')
    return count


def entrypoint(params:ExperimentParameters, response:ExpResult):
    response.result = bytearray(10)

    # Read parameters
    p = params.argument_bytes
    l = len(p)
    p_mode   = int.from_bytes(p[0:1], 'little') & 0xff if l >= 1 else 0
    p_bits   = int.from_bytes(p[1:3], 'little') & 0xffff if l >= 3 else 0
    p_a      = int.from_bytes(p[3:4], 'little') & 0xff if l >= 4 else 0
    p_b      = int.from_bytes(p[4:5], 'little') & 0xff if l >= 5 else 0
    p_expect = int.from_bytes(p[5:7], 'little') & 0xffff if l >= 7 else 0
    p_loop   = int.from_bytes(p[7:10], 'little') & 0xffffff if l >= 10 else 0
    #print(f'mode={p_mode:02x} bits={p_bits:04x} a={p_a:02x} b={p_b:02x} expect={p_expect:04x} loop={p_loop:06x}')

    # get the TT DemoBoard object from params passed in
    tt = params.tt 

    # Select a design, this isn't used but potentially could alter temperature
    # through power draw
    tt.clock_project_stop()

    tt.pins.safe_bidir()
    tt.mode = 1 # ttboard.mode.RPMode.ASIC_RP_CONTROL

    tt.rst_n(False)
    tt.clk(False)
    tt.ui_in.value = 0 # ui_in = 8'b0
    tt.uio_in.value = 0  # uio_in = 8'b0
    tt.uio_oe_pico = 0 # safe_bidir()
    time.sleep_ms(1) # discharge settle

    # 614 = tt_um_dlmiles_muldiv8
    # 616 = tt_um_dlmiles_muldiv8_sky130faha
    DESIGN_ID = 614
    tt.shuttle.reset_and_clock_mux(DESIGN_ID)
    time.sleep_ms(1)
    tt.clock_project_once()
    tt.clock_project_once()
    tt.uio_oe_pico = 0b11001001
    clock_on(tt)
    tt.rst_n(True)

    r = 0
    c = 0
    count = 0
    good_count = 0

    uio_in = 0
    maxloop = p_loop
    # Some defaults for all zero input (iterate once for 0 * 0 = 0)
    if p_mode == 0 and p_bits == 0 and p_a == 0 and p_b == 0 and p_loop == 0:
        maxloop = 1 # default (all data zero, do 1 iteration)
        p_bits = 0x08 # MUL/UNS=0 and REG=0x08
    #print(f'entrypoint INIT loop={maxloop}')

    # project should be synced by default after reset
    clock_cycle(tt)
    clock_cycle(tt)

    populate_response(response.result, count, r, c, good_count, 1) # checkpoint #1

    while params.keep_running and maxloop > 0:
        #print(f'entrypoint LOOP loop={maxloop}')
        if maxloop > 0:
            maxloop -= 1

        b_set   = p_bits & 0xff
        b_reset = (~(p_bits >> 8)) & 0xff # inverted reset mask
        #uio_in = tt.uio_in.value
        uio_in |= b_set
        uio_in &= b_reset
        uio_in = addr_set(tt, uio_in, False) # bit0=0 A0
        #print(f'set={b_set:02x} reset={b_reset:02x} uio_in={uio_in:02x}')

        tt.ui_in.value = p_a
        clock_off(tt)
        clock_on(tt)

        tt.ui_in.value = p_b
        uio_in = addr_set(tt, uio_in, True) # bit0=1 A1
        clock_off(tt)
        clock_on(tt)

        r_b = tt.uo_out.value
        c_b = tt.uio_out.value
        #print(f'r_b={r_b} c_b={c_b} uio_in={tt.uio_in.value}={uio_in:02x}')

        uio_in = addr_set(tt, uio_in, False) # bit0=0 A0

        r_a = tt.uo_out.value
        c_a = tt.uio_out.value
        #print(f'r_a={r_a} c_a={c_a} uio_in={tt.uio_in.value}={uio_in:02x}')

        r = (int(r_a) & 0xff) | ((int(r_b) << 8) & 0xff00)
        c = (int(c_a) & 0xff) | ((int(c_b) << 8) & 0xff00)

        if count < 0xffffff: # no wrap
            count += 1
        if r == p_expect:
            if good_count < 0xffffff: # no wrap
                good_count += 1
            m = 'PASS'
        else:
            m = 'FAIL'

        #print(f'{m}: r={r:04x} expect={p_expect:04x}')

        #print(f'ANSWER r={r:04x} c={c:04x} {good_count}/{count}')
        populate_response(response.result, count, r, c, good_count, 2) # checkpoint #2


    populate_response(response.result, count, r, c, good_count, 3) # checkpoint #3
    #print(f'entrypoint EXIT loop={maxloop}')
