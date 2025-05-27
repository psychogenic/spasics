#!/usr/bin/env python3
from microcotb.types.logic_array import LogicArray
from microcotb.types.range import Range
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

# Simple program calculating the fibonacci sequence with RISC-V Assembly
# The program stored in CEJMU_RV.mem is:
#     addi x5, x0, 160 # base address
#     addi x6, x0, 6

#     addi x7, x0, 1
#     addi x8, x0, 1
#     addi x9, x0, 1

# loop:
#     add x9, x8, x7
#     add x7, x0, x8
#     add x8, x0, x9

#     sw x8, 0(x5)

#     addi x5, x5, 4
#     addi x6, x6, -1
#     bne x0, x6, loop

# end:
#     addi x1, x0, 1
#     bne x1, x0, end
#
# The first five numbers are stored in the result object, so we can verify if
# the CPU computed everything correctly

class CEJMU_RV:
    def __init__(self, tt):
        self.tt = tt

        # Enabling the design
        tt.shuttle.tt_um_cejmu_riscv.enable()

        # Initial Reset
        tt.reset_project(True)
        tt.clock_project_once()
        tt.clock_project_once()
        tt.clock_project_once()
        tt.reset_project(False)

        # Clearing MISO Pin
        tt.pins.ui_in.value = 0

        # Setting attributes of the TB
        self.mem = {
                0: LogicArray(0b00001010000000000000001010010011, Range(31, "downto", 0)),
                1: LogicArray(0b00000000011000000000001100010011, Range(31, "downto", 0)),
                2: LogicArray(0b00000000000100000000001110010011, Range(31, "downto", 0)),
                3: LogicArray(0b00000000000100000000010000010011, Range(31, "downto", 0)),
                4: LogicArray(0b00000000000100000000010010010011, Range(31, "downto", 0)),
                5: LogicArray(0b00000000011101000000010010110011, Range(31, "downto", 0)),
                6: LogicArray(0b00000000100000000000001110110011, Range(31, "downto", 0)),
                7: LogicArray(0b00000000100100000000010000110011, Range(31, "downto", 0)),
                8: LogicArray(0b00000000100000101010000000100011, Range(31, "downto", 0)),
                9: LogicArray(0b00000000010000101000001010010011, Range(31, "downto", 0)),
                10: LogicArray(0b11111111111100110000001100010011, Range(31, "downto", 0)),
                11: LogicArray(0b11111110011000000001010011100011, Range(31, "downto", 0)),
                12: LogicArray(0b00000000000100000000000010010011, Range(31, "downto", 0)),
                13: LogicArray(0b11111110000000001001111011100011, Range(31, "downto", 0))
        }

        self.spi_counter = 18
        self.spi_addr = LogicArray(0, Range(15, "downto", 0))
        self.spi_data = LogicArray(0, Range(31, "downto", 0))
        self.spi_state = "addr"
        self.spi_write = False

    def do_spi(self):
        mosi = self.tt.uo_out.value[0]
        if self.tt.uo_out.value[2] == 0:
            # Recv address
            if self.spi_state == "addr":
                if self.spi_counter >= 16:
                    if mosi == 1:
                        self.spi_write = True
                    else:
                        self.spi_write = False

                    self.spi_counter -= 1
                elif self.spi_counter == 0:
                    self.spi_addr[self.spi_counter] = mosi
                    self.spi_counter = 32

                    if self.spi_write:
                        self.spi_state = "rx"
                        self.spi_counter = 33
                    else:
                        self.spi_state = "tx"

                else:
                    self.spi_addr[self.spi_counter] = mosi
                    self.spi_counter -= 1

            # Recv data
            elif self.spi_state == "rx":
                if self.spi_counter > 31:
                    self.spi_counter -= 1

                elif self.spi_counter == 0:
                    self.spi_data[self.spi_counter] = mosi
                    self.spi_state = "addr"

                    self.mem[int(self.spi_addr)] = self.spi_data
                else:
                    self.spi_data[int(self.spi_counter)] = mosi
                    self.spi_counter -= 1

            # Trx data
            else:
                if self.spi_counter > 31:
                    self.spi_counter -= 1

                elif self.spi_counter == 0:
                    self.tt.ui_in.value[0] = self.mem[int(self.spi_addr)][self.spi_counter]
                    self.spi_state = "addr"
                else:
                    self.tt.ui_in.value[0] = self.mem[int(self.spi_addr)][self.spi_counter]
                    self.spi_counter -= 1
        else:
            self.spi_counter = 18
            self.spi_addr = LogicArray(0, Range(15, "downto", 0))
            self.spi_data = LogicArray(0, Range(31, "downto", 0))
            self.spi_state = "addr"
            self.spi_write = False

    def run_program(self, params, response, num_iterations):
        response.result = bytearray(10)
        for i in range(num_iterations):
            if not params.keep_running:
                self.tt.clock_project_stop()
                # Indicate in the result that we were told to stop
                response.result = bytearray(10)
                response.result[0] = 0xFF
                return

            self.tt.clock_project_once()
            self.do_spi()

            response.result[0] = self.get_mem_or_zero(160) % 2**8
            response.result[1] = self.get_mem_or_zero(164) % 2**8
            response.result[2] = self.get_mem_or_zero(168) % 2**8
            response.result[3] = self.get_mem_or_zero(172) % 2**8
            response.result[4] = self.get_mem_or_zero(176) % 2**8
            response.result[5] = self.get_mem_or_zero(180) % 2**8

    def get_mem_or_zero(self, addr):
        if self.mem.get(addr) is None:
            return 0
        else:
            return int(self.mem.get(addr))


def test_cpu(params:ExperimentParameters, response:ExpResult, num_iterations:int=5000):
    cpu = CEJMU_RV(params.tt)
    cpu.run_program(params, response, num_iterations)

    params.tt.clock_project_stop()
    return
