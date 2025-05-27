# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Uri Shaked

from spasic.experiment.experiment_parameters import ExperimentParameters
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.tt_um_urish_spell.spell_controller import SpellController


def test_spasics_spell(params: ExperimentParameters, response: ExpResult):
    # Result is up to 10 bytes
    response.result = bytearray(10)

    tt = params.tt

    # Set bidirs to inputs
    tt.uio_oe_pico.value = 0
    tt.shuttle.tt_um_urish_spell.enable()
    tt.clock_project_stop()

    spell_ctrl = SpellController(tt)
    tt.reset_project(True)
    tt.clock_project_once()
    tt.reset_project(False)

    # Find the source code for the test program in spasic.spl
    # fmt: off
    test_program = [
        127, 55, 119, 36, 115, 67, 73, 83, 65, 112, 
        115, 7, 120, 56, 119, 12, 64, 122,
    ]
    # fmt: on
    response.result[0] = 1 # Writing the program to memory
    spell_ctrl.write_program(test_program)

    print("Casting the SPELL...")
    response.result[0] = 2 # Executing the program
    spell_ctrl.execute(False)
    last_uio_in = tt.uio_in.value
    resp_index = 0
    while not spell_ctrl.stopped() and params.keep_running:
        tt.clock_project_once()
        if resp_index < len(response.result) and last_uio_in != tt.uio_in.value:
            last_uio_in = tt.uio_in.value
            response.result[resp_index] = last_uio_in
            resp_index += 1
