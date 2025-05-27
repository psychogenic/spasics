# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Uri Shaked

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters


def run_experiment(params: ExperimentParameters, response: ExpResult):

    try:
        import spasic.experiment.tt_um_urish_spell.bewitch

        spasic.experiment.tt_um_urish_spell.bewitch.test_spasics_spell(params, response)

    except Exception as e:
        response.exception = e
    else:
        response.completed = True
    return
