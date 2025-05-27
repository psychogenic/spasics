# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Ken Pettit

from ttboard.cocotb.dut import DUT
from ttboard.demoboard import DemoBoard
import machine
import time
import sys
import select

REG_EXEC = 0
REG_ACC = 1
REG_PC = 2
REG_SP = 3
REG_RA = 4
REG_IX = 5
REG_RAM = 6
REG_BREAK = 8
REG_IO = 0x1b
REG_SPI_QSPI = 0x17
REG_CACHE = 0x1d
REG_SPI_MODE = 0x1e

class LisaController(DUT):
  def __init__(self, tt: DemoBoard):
    super().__init__("LISA`")
    self.tt = tt
    self.uart = machine.UART(0, baudrate=230400, tx=machine.Pin(12), rx=machine.Pin(13))
    self.halted = True

  def writeStr(self, s):
    self.uart.write(s.encode('utf-8'))

  def readLine(self, timeout_ms=100):
    line = b''
    start = time.ticks_ms()
    while True:
      if self.uart.any():
        c = self.uart.read(1)
        line += c
        if c == b'\r':
          break
        if c == b's' and line != b'lis':
          self.halted = True
          break

      if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
        break
    return line.decode('utf-8').strip('\n\r')

  def get_ver(self):
    for x in range(5):
      self.writeStr('\n')
      s = self.readLine()
      s = self.readLine()
    self.writeStr('v')
    ver = self.readLine()
    return ver

  def write_reg(self, reg: int, value: int):
    self.writeStr(f'w{reg:02x}{value:04x}\n\n')
    s = self.readLine()

  def read_reg(self, reg: int):
    self.writeStr(f'r{reg:02x}\n')
    s = self.readLine()
    try:
      val = int(s, 16)
    except:
      val = 0xDEAD

    return val

  def reset(self):
    self.writeStr('t')

  def step(self):
    self.write_reg(REG_EXEC, 5)

  def cont(self, run_delay=0.0):
    self.writeStr(f'w000000\n')
    self.halted = False
    if run_delay > 0.0:
      time.sleep(run_delay)

  def set_breakpoint(self, n, addr):
    self.write_reg(REG_BREAK + n, 0x8000 | addr)

  def clear_breakpoint(self, n):
    self.write_reg(REG_BREAK + n, 0)

  def await_break(self, timeout = 1.0):
    if self.halted:
      return

    start = time.ticks_ms()
    while True:
      if self.uart.any():
        c = self.uart.read(1)
        if c == b's':
          self.halted = True
          break

      if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
        print("LISA did not halt")
        break

  def get_pc(self):
    return self.read_reg(REG_PC)

  def set_pc(self, value: int):
    self.write_reg(REG_PC, value)

  def get_sp(self):
    return self.read_reg(REG_SP)

  def set_sp(self, value: int):
    self.write_reg(REG_SP, value)

  def get_ix(self):
    return self.read_reg(REG_IX)

  def set_ix(self, value: int):
    self.write_reg(REG_IX, value)

  def get_acc(self):
    return self.read_reg(REG_ACC) & 0xFF

  def set_acc(self, value: int):
    acc = self.read_reg(REG_ACC) & 0xFF00;
    self.write_reg(REG_ACC, acc | value)

  def get_ram(self, addr, len):
    d = []
    ix = self.get_ix()
    for i in range(len):
      self.set_ix(addr + i)
      d.append(self.read_reg(REG_RAM))
    self.set_ix(ix)
    return d

  def dump_ram(self):
  # Dump the final contents of DFFRAM
    print("DFFRAM Contents:")
    d = self.get_ram(0, 128)
    inrow = 0
    addr = 0
    for b in d:
      if inrow == 0:
        print(f'0x{addr:02x}  ', end='')
      print(f'{b:02x} ', end='')
      inrow += 1
      if inrow == 16:
        print('')
        inrow = 0
      addr += 1

# vim: sw=2 ts=2 et
