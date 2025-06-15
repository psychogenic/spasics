'''
Created on Jun 12, 2025

@author: Mike Bell
@copyright: Copyright (C) 2025 Michael Bell

This experiment measures the temperature using the RP2040's on board 
temperature sensor, while optionally clocking running a selected TT design

The returned values are raw ADC readings, to turn these into temperatures
apply the formula:
  temp_in_C = 27 - ((reading * 3.3 / 65536) - 0.706) / 0.001721
'''
import time
import machine
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

class Thermometer:
    def __init__(self):
        self.sensor = machine.ADC(4)
        self.readings = 0
        self.min_value = 0
        self.max_value = 0
        self.total = 0
        self.cur_value = self.sensor.read_u16()

    def take_reading(self):
        self.cur_value = self.sensor.read_u16()
        if self.readings == 0:
            self.min_value = self.max_value = self.cur_value
        else:
            if self.min_value > self.cur_value:
                self.min_value = self.cur_value
            if self.max_value < self.cur_value:
                self.max_value = self.cur_value
        self.total += self.cur_value
        self.readings += 1
    
    def populate_response(self, response):
        response.result[0:2] = self.cur_value.to_bytes(2, 'little')
        response.result[2:4] = self.min_value.to_bytes(2, 'little')
        response.result[4:6] = self.max_value.to_bytes(2, 'little')
        response.result[6:8] = (self.total // self.readings).to_bytes(2, 'little')
        response.result[8:10] = (self.readings // 10).to_bytes(2, 'little')


def test_temperature(params:ExperimentParameters, response:ExpResult):
    # Response structure will be:
    # Current, min, max, mean, iterations / 10, all 2 bytes each
    response.result = bytearray(10)

    # Read parameters
    num_iterations = int.from_bytes(params.argument_bytes[0:4], 'little')
    hundredths_per_iteration = int.from_bytes(params.argument_bytes[4:6], 'little')
    select_tt_design = int.from_bytes(params.argument_bytes[6:8], 'little')
    clock_khz = int.from_bytes(params.argument_bytes[8:10], 'little')

    # Initialize thermometer
    therm = Thermometer()

    # get the TT DemoBoard object from params passed in
    tt = params.tt 

    # Select a design, this isn't used but potentially could alter temperature
    # through power draw
    tt.shuttle[select_tt_design].enable()
    if clock_khz != 0:
        tt.clock_project_PWM(1000 * clock_khz)

    while True:
        therm.take_reading()
        therm.populate_response(response)
        time.sleep_ms(hundredths_per_iteration * 10)

        if num_iterations > 0:
            num_iterations -= 1
            if num_iterations == 0:
                break
