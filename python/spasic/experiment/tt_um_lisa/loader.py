# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Ken Pettit

from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def run_experiment(params: ExperimentParameters, response: ExpResult):

  try:
    import spasic.experiment.tt_um_lisa.dominISA
    spasic.experiment.tt_um_lisa.dominISA.tickle_her_fancy(params, response)

  except Exception as e:
    response.exception = e
  else:
    response.completed = True
  return
