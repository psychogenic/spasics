'''
Created on May 26, 2025

@author: Ryan Harrigan, Rachel Moheban
@copyright: Copyright (C) 2025 Ryan Harrigan, https://changeprogramming.com
'''
import random
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

# family and friend aliases
messages = [
    "gauss",
    "picklejar",
    "apiaceae",
    "compost",
    "jp_67",
    "jamacosin",
    "ms_muffet",
    "QVXAGNDAUK",
    "2GradeFren",
    "Jyn&Maz"
]

def inspect_bottle(_params:ExperimentParameters, response:ExpResult):
    message = uncork_bottle()

    # clamp to 10 characters (max 10 bytes)
    shunted = message[:10]

    # rjust in uPython
    padded = "{:>10}".format(shunted)

    # tx payload
    response.result = bytes(padded, "utf8")

    return

# @TODO get number from tt_um_rng
def uncork_bottle(idx: int = random.randint(0, len(messages) - 1)):
    _idx = idx

    # prevent out-of-bounds
    if (idx < 0 or idx > len(messages)):
        _idx = random.randint(0, len(messages) - 1)

    return messages[idx]
