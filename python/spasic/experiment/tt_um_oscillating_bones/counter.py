'''
Created on May 8, 2025

@author: Matt Venn
@copyright: Copyright (C) 2025 Matt Venn

RP2040 frequency counter code is from:

https://github.com/intel00000/pi_pico_pio_pwm_frequency_measurement

'''
import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

from machine import Pin, PWM, freq
from rp2 import asm_pio, StateMachine, PIO
import time

# Pin to generate the PWM signal, connect this pin to the INPUT_PULSE_PIN_ABSOLUTE pin
PWM_OUTPUT_PIN = 21
# Pin to measure the frequency of the PWM signal
INPUT_PULSE_PIN = 8
# Pin to generate the timing pulses
TIMING_PULSE_PIN = 22
# Pin to set the side-set pin
SIDESET_PIN = 23
CPU_FREQUENCY = 125_000_000  # 125 MHz
TIMING_PULSE_RATIO = 0x4  # 8 timing pulses for 1 gate time
TIMING_PULSE_FREQUENCY = 8  # 8 Hz

TIMING_PULSE_SM_ID = 0
PULSE_COUNTER_SM_ID = 1


# Moving average filter configuration
N = 64  # Moving average window size
index = 0
total = 0

# call like this to set the window to 8: runner.launch(3,[8])
def test_counter(params:ExperimentParameters, response:ExpResult, window_size:int=16):
    # first byte is number of times we've got a measurement
    # next 3 bytes is the average of all the measurements
    response.result = bytearray(4)
    
    # allocate moving average buffer
    global N, buffer, index, total
    index = 0
    total = 0
    N = window_size
    buffer = [0] * N
    print(f"moving average window is {N}")

    # get the TT DemoBoard object from params passed in
    tt = params.tt 
    
    # Use the TT object to load your design
    tt.shuttle.tt_um_oscillating_bones.enable()
    
    # Likely you want to clock it yourself, stop any auto-clocking
    tt.clock_project_stop()
    
    # set bidirs to inputs
    tt.uio_oe_pico.value = 0 
    
    # Generate test PWM signal on PWM_OUTPUT_PIN
    pwm_test_signal = PWM(Pin(PWM_OUTPUT_PIN, Pin.OUT))
    pwm_test_signal.freq(5000000)  # Set the frequency of the PWM signal
    pwm_test_signal.duty_u16(32768)  # Set duty cycle to 50%

    # Initialize the pulse counter for the timer method
    pulse_counter = PulseCounter()

    # start the pulse counter
    pulse_counter.reset()
    pulse_counter.start()
    print("pulse counter started")

    # make measurements continuously
    loops = 0
    while params.keep_running:
        timing_pulse_count = pulse_counter.read_timing_count()
        if timing_pulse_count == 1:
            pulse_count = pulse_counter.read_pulse_count()
            avg = update_average(pulse_count)
            loops += 1
            response.result[0] = loops
            response.result[1:4] = avg.to_bytes(3, 'little')
            print(loops, pulse_count, avg)
        elif timing_pulse_count == -1:
            continue

    # shutdown
    print("stopping pulse counter")
    pulse_counter.stop()
    print("stopping pwm")
    pwm_test_signal.deinit()

def update_average(new_value):
    global index, total

    # Subtract old value, add new one
    total -= buffer[index]
    total += new_value

    # Store new value in circular buffer
    buffer[index] = new_value
    index = (index + 1) % N

    # Compute average
    avg = total // N
    return avg

# PIO program to count pulses, the gate time is controlled a side-set pin set by another PIO program
@asm_pio(autopush=True, push_thresh=32, fifo_join=PIO.JOIN_RX)
def pulse_counter_pio(
    sideset_pin=SIDESET_PIN,
):
    label("start")
    set(x, 0)  # Set the x register to 0, this is the counter register for the pulses

    # measuring the falling edge of the side-set pin
    wait(1, gpio, sideset_pin)
    wait(0, gpio, sideset_pin)

    # start counting the pulses
    label("count")
    wait(0, pin, 0)  # Measure the rising edge of the input pin
    wait(1, pin, 0)
    jmp(x_dec, "check_sideset_pin")  # Decrement counter and jump to check_sideset_pin
    label("check_sideset_pin")
    jmp(pin, "shift")  # If side-set is high, jump to shift
    jmp("count")  # If side-set is low, continue count

    label("shift")
    in_(x, 32)  # Shift the x register to the ISR
    jmp("start")  # Restart the program


# A second pio program to set a side-set pin, initialize the side-set pin to high
@asm_pio(
    sideset_init=PIO.OUT_HIGH, autopush=True, push_thresh=32, fifo_join=PIO.JOIN_RX
)
def timing_pulse_pio(
    sm_id=TIMING_PULSE_SM_ID,
    pulse_pin=INPUT_PULSE_PIN,
    timing_ratio=TIMING_PULSE_RATIO,
):
    label("start")
    set(x, timing_ratio)  # Set the x register to timing_ratio
    # we will wait for timing_ratio times timing pulses before setting the side-set pin
    set(y, 0)  # set the y register to 0 to compare with the x register

    wait(0, gpio, pulse_pin)
    wait(1, gpio, pulse_pin)  # synchronize the timing pulse with the actual pulse
    # set the irq to signal interrupt to start the timing pulse, this ensure timing pulse is synchronized with the pulse
    irq(rel(sm_id))
    wait(1, pin, 0)
    wait(0, pin, 0)  # wait for the timing pulse to go low to synchronize the timing
    # set the side-set pin to 0 to let the pulse counter know that the gate time has started
    nop().side(0)

    label("loop")
    wait(1, pin, 0)  # Wait for high pulse on input pin
    wait(0, pin, 0)  # Wait for low pulse on input pin

    # for debugging purposes, move the x to the isr
    in_(x, 32)  # Shift the x register to the ISR

    # One pulse has been received, decrement the x register
    jmp(x_dec, "check_x")  # Decrement x and jump to check_x
    label("check_x")
    jmp(x_not_y, "loop")  # if x is not equal to y, jump back to the loop
    jmp("start").side(1)  # else set the side-set pin to 1 and jump back to the start


# Class to handle the pulse counting
class PulseCounter:
    def __init__(
        self,
        pulse_counter_pio_sm_id=PULSE_COUNTER_SM_ID,
        timing_pulse_pio_sm_id=TIMING_PULSE_SM_ID,
        pulse_pin=INPUT_PULSE_PIN,
        timing_pin=TIMING_PULSE_PIN,
        sideset_pin=SIDESET_PIN,
        cpu_frequency=CPU_FREQUENCY,
        timing_pulse_frequency=TIMING_PULSE_FREQUENCY,
        timing_pulse_ratio=TIMING_PULSE_RATIO,
    ) -> None:
        freq(cpu_frequency)  # Set the CPU frequency
        print(f"cpu frequency set to: {freq()} Hz")
        self.pulse_counter_pio_sm_id = pulse_counter_pio_sm_id  # pulse counter sm id
        self.timing_pulse_pio_sm_id = timing_pulse_pio_sm_id  # timing pulse sm id
        StateMachine(self.pulse_counter_pio_sm_id).active(0)  # clear all state machines
        StateMachine(self.pulse_counter_pio_sm_id).active(0)  # clear all state machines
        self.pulse_pin = Pin(pulse_pin, Pin.IN, Pin.PULL_DOWN)  # input pulse pin
        self.timing_pin = Pin(timing_pin, Pin.OUT)  # timing pulse pin
        self.timing_pin_pwm = PWM(self.timing_pin)  # timing pulse pin pwm object
        self.sideset_pin = Pin(sideset_pin, Pin.OUT)  # sideset pin
        self.timing_pulse_frequency = timing_pulse_frequency  # timing pulse frequency
        self.timing_pulse_ratio = timing_pulse_ratio  # timing pulse ratio
        # setup the pulse counter state machine
        self.pulse_counter_pio_sm = StateMachine(
            self.pulse_counter_pio_sm_id,
            pulse_counter_pio,
            freq=freq(),
            in_base=self.pulse_pin,
            jmp_pin=self.sideset_pin,
            sideset_base=self.sideset_pin,
        )
        # setup the timing pulse state machine
        self.timing_pulse_pio_sm = StateMachine(
            self.timing_pulse_pio_sm_id,
            timing_pulse_pio,
            freq=freq(),
            in_base=self.timing_pin,
            sideset_base=self.sideset_pin,
        )
        # get the irq object for the timing pulse state machine
        self.timing_pulse_pio_sm.irq(handler=self.callback, trigger=1)
        print(
            f"Pulse Counter State Machine ID: {self.pulse_counter_pio_sm_id}, Timing Pulse State Machine ID: {self.timing_pulse_pio_sm_id}"
        )
        # generate the timing pulses
        self.timing_interval_ms = self.timing_pulse_generator()

    def callback(self, sm):
        # reinit the timing pulse signal
        self.timing_pulse_generator(message=False)

    def read_pulse_count(self):
        if self.pulse_counter_pio_sm.rx_fifo() == 0:
            return -1
        else:
            pulse_count = self.pulse_counter_pio_sm.get()  # Get value from the FIFO
            return (0x100000000 - pulse_count) & 0xFFFFFFFF  # flip the value

    def read_timing_count(self):  # for debugging purposes
        if self.timing_pulse_pio_sm.rx_fifo() == 0:
            return -1
        else:
            return self.timing_pulse_pio_sm.get()

    def reset(self):
        self.pulse_counter_pio_sm.restart()
        self.timing_pulse_pio_sm.restart()

    def start(self):
        self.timing_pulse_pio_sm.active(1)
        self.pulse_counter_pio_sm.active(1)

    def stop(self):
        self.pulse_counter_pio_sm.active(0)
        self.timing_pulse_pio_sm.active(0)

    def timing_pulse_generator(
        self,
        message=True,
    ):
        self.timing_pin_pwm.deinit()
        self.timing_pin_pwm.freq(self.timing_pulse_frequency)
        self.timing_pin_pwm.duty_u16(32768)
        timing_interval_ms = (
            1000 / self.timing_pulse_frequency * self.timing_pulse_ratio
        )
        if message:
            print(
                f"Timing Pulse Frequency: {self.timing_pulse_frequency} Hz, Timing Interval: {timing_interval_ms} ms"
            )
        return timing_interval_ms


