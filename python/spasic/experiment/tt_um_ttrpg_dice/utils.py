def inflate(results):
    d4  = [(results[0] % 4) + 1 , (results[1] % 4) + 1 , (results[2] % 4) + 1 ]
    d6  = [((results[0] >> 2) % 8 ) + 1, ((results[1] >> 2) % 8 ) + 1, ((results[2] >> 2) % 8 ) + 1 ]
    d8  = [((results[0] >> 5) % 8 ) + 1,((results[1] >> 5) % 8 ) + 1,((results[2] >> 5) % 8 ) + 1 ]
    d10 = [(results[3]       % 16 ) + 1,(results[3] >> 4  % 16 ) + 1,(results[4]       % 16 ) + 1]
    d12 = [(results[6]       % 16 ) + 1,(results[8]       % 16 ) + 1]
    d20 = [(results[4] >> 4) + (results[5] >> 7) * 16 + 1,(results[4] >> 6) + (results[7] >> 7) * 16 + 1,(results[4] >> 8) + (results[9] >> 7) * 16 + 1]
    d100 = [results[5] % 128,results[7] % 128,results[9] % 128]
    return [ d4, d6, d8, d10, d12, d20, d100 ]


def check():
    print(runner.experiment_results_as_str)
    print(inflate(runner.experiment_result))


from spasic.experiment_runner import ExperimentRunner
runner = ExperimentRunner()
runner.launch(11)

check()
