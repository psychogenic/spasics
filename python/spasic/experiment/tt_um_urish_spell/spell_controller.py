# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Uri Shaked

from ttboard.cocotb.dut import DUT
from ttboard.demoboard import DemoBoard


REG_PC = 0
REG_SP = 1
REG_EXEC = 2
REG_STACK_TOP = 3


class SpellController(DUT):
    def __init__(self, tt: DemoBoard):
        super().__init__("Spell")
        self.tt = tt
        self.i_run = self.new_bit_attribute("i_run", tt.ui_in, 0)
        self.i_step = self.new_bit_attribute("i_step", tt.ui_in, 1)
        self.i_load = self.new_bit_attribute("i_load", tt.ui_in, 2)
        self.i_dump = self.new_bit_attribute("i_dump", tt.ui_in, 3)
        self.i_shift_in = self.new_bit_attribute("i_shift_in", tt.ui_in, 4)
        self.i_reg_sel = self.new_slice_attribute("i_reg_sel", tt.ui_in, 6, 5)

        self.o_cpu_sleep = self.new_bit_attribute("o_cpu_sleep", tt.uo_out, 0)
        self.o_cpu_stop = self.new_bit_attribute("o_cpu_stop", tt.uo_out, 1)
        self.o_wait_delay = self.new_bit_attribute("o_wait_delay", tt.uo_out, 2)
        self.o_shift_out = self.new_bit_attribute("o_shift_out", tt.uo_out, 3)

        self.i_run.value = 0
        self.i_step.value = 0
        self.i_load.value = 0
        self.i_dump.value = 0
        self.i_shift_in.value = 0
        self.i_reg_sel.value = 0

    def ensure_cpu_stopped(self):
        while int(self.o_cpu_stop) == 0:
            self.tt.clock_project_once()

    def stopped(self):
        return int(self.o_cpu_stop) == 1

    def sleeping(self):
        return int(self.o_cpu_sleep) == 1

    def write_reg(self, reg: int, value: int):
        for i in range(8):
            self.i_shift_in.value = (value >> (7 - i)) & 1
            self.tt.clock_project_once()
        self.i_reg_sel.value = reg
        self.i_load.value = 1
        self.tt.clock_project_once()
        self.i_load.value = 0
        self.tt.clock_project_once()

    def read_reg(self, reg: int):
        self.i_reg_sel.value = reg
        self.i_dump.value = 1
        self.tt.clock_project_once()
        self.i_dump.value = 0
        value = 0
        for i in range(8):
            self.tt.clock_project_once()
            value |= int(self.o_shift_out) << (7 - i)
        return value

    def execute(self, wait=True):
        self.ensure_cpu_stopped()
        self.i_run.value = 1
        self.i_step.value = 0
        self.tt.clock_project_once()
        self.i_run.value = 0
        self.tt.clock_project_once()
        if wait:
            self.ensure_cpu_stopped()

    def single_step(self):
        self.ensure_cpu_stopped()
        self.i_run.value = 1
        self.i_step.value = 1
        self.tt.clock_project_once()
        self.i_step.value = 0
        self.i_run.value = 0
        self.tt.clock_project_once()
        self.ensure_cpu_stopped()

    def exec_opcode(self, opcode):
        int_opcode = ord(opcode) if type(opcode) == str else int(opcode)
        self.ensure_cpu_stopped()
        self.write_reg(REG_EXEC, int_opcode)
        self.ensure_cpu_stopped()

    def read_stack_top(self):
        return self.read_reg(REG_STACK_TOP)

    def push(self, value: int):
        self.ensure_cpu_stopped()
        self.write_reg(REG_STACK_TOP, value)

    def read_pc(self):
        return self.read_reg(REG_PC)

    def set_pc(self, value: int):
        self.write_reg(REG_PC, value)

    def read_sp(self):
        return self.read_reg(REG_SP)

    def set_sp(self, value: int):
        self.write_reg(REG_SP, value)

    def set_sp_read_stack(self, index: int):
        self.set_sp(index)
        return self.read_stack_top()

    def write_progmem(self, addr: int, value: Union[int, str]):
        """
        Writes a value to progmem by executing an instruction on the CPU.
        """
        self.ensure_cpu_stopped()
        int_value = ord(value) if type(value) == str else int(value)
        self.write_reg(REG_STACK_TOP, int_value)
        self.write_reg(REG_STACK_TOP, addr)
        self.write_reg(REG_EXEC, ord("!"))

    def write_program(self, opcodes, offset=0):
        for index, opcode in enumerate(opcodes):
            self.write_progmem(offset + index, opcode)
