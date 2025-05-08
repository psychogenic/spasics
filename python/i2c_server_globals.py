from spasic.fs.filesystem import FSAccess
from spasic.variables.variables import Variables
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters
from ttboard.demoboard import DemoBoard

FileSystem = FSAccess()
ERes = ExpResult()
ExpArgs = ExperimentParameters(DemoBoard.get())
ClientVariables = Variables()
PendingDataIn = [bytearray(9), bytearray(9), bytearray(9), bytearray(9), bytearray(9), bytearray(9)]
PendingDataNum = 0
PendingDataOut = []
ExperimentRun = False
LastTimeSyncMessageTime = -1
LastTimeSyncValue = 0