from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def run_experiment(params:ExperimentParameters, response:ExpResult):

    # always wrap everything in a try block
    try:
        # import HERE, inside the function,
        # such that loading all the experiment runners doesn't
        # eat a ton of memory by pre-importing everything
        import spasic.experiment.wokwi_universal_gates_049.test
        # run that experiment
        spasic.experiment.wokwi_universal_gates_049.test.run_test(params, response, num_iterations=16)

    except Exception as e:
        # an exception occurred...
        # let the server know about it
        response.exception = e
    else:
        # we get here, all went well
        # mark the experiment as completed
        response.completed = True
    return