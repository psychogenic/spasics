from spasic.experiment.tt_um_ttrpg_dice.sevenseg import SevenSegmentDecode
import time
import random

def roll(tt, button,randomize):
    freq = tt.auto_clocking_freq
    tt.ui_in = button
    time.sleep_ms(20)
    if (randomize != 0):
        time.sleep_us(random.randint(1,1200))
    tt.ui_in = 0
    time.sleep_us(10)
    tt.clock_project_stop()
    tt.pins.project_clk_driven_by_RP2040(True)
    tt.clk(1)
    temp = tt.uo_out
    result = SevenSegmentDecode(temp)
    tt.clk(0)
    temp=tt.uo_out
    result += 10 * SevenSegmentDecode(temp)
    tt.clock_project_PWM(freq)
    return result
