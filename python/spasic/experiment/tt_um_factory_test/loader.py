'''
Created on Apr 28, 2025

@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''


def run_experiment(response):
    print("Made it to loader, importing")
    try:
        import spasic.experiment.tt_um_factory_test.experiment_1 as exp1
        print("Import done, calling test")
        exp1.test_loopback(response, num_iterations=5)
    except Exception as e:
        response.exception = e 
    else:
        response.completed = True
    return