# SPDX-License-Identifier: Apache2.0
# Copyright (C) 2025 Ken Pettit

import rp2
from machine import Pin, mem32
import time

@rp2.asm_pio(
  out_init=rp2.PIO.OUT_LOW,
  out_shiftdir=rp2.PIO.SHIFT_LEFT,
  fifo_join = rp2.PIO.JOIN_TX,
  autopull=True,
  pull_thresh=32
)
def sram_write():
  # ISR is loaded with SM specific JMP to one of the entry points below
  mov(exec, isr)

  # SM0 Entry
  wait(1, irq, 0)
  irq(clear, 0)
  jmp("cmd_entry")

  # SM1 Entry
  wait(1, irq, 1)
  irq(clear, 1)
  jmp("cmd_entry")

  # SM2 Entry
  wait(1, irq, 2)
  irq(clear, 2)
  jmp("cmd_entry")

  # SM3 Entry
  wait(1, irq, 3)
  irq(clear, 3)

  # Load Y to loop for 4 transactions (8-deep FIFO, 2 words per transfer)
  label("cmd_entry")
  set(y, 3)
  
  # Read the 24 bit command (8-bit command, 16-bit address)
  label("transact_loop")
  set(x, 23)
  label("cmd_addr_loop")
  wait(0, pin, 0)
  wait(1, pin, 0)
  jmp(x_dec, "cmd_addr_loop")

  # First FIFO WORD
  set(x, 31)
  label("write_loop1")
  wait(0, pin, 0)
  out(pins, 1)
  wait(1, pin, 0)
  jmp(x_dec, "write_loop1")

  # Second FIFO WORD
  set(x, 31)
  label("write_loop2")
  wait(0, pin, 0)
  out(pins, 1)
  wait(1, pin, 0)
  jmp(x_dec, "write_loop2")

  # Loop for 4 transactions per SM FIFO
  jmp(y_dec, "transact_loop")

  # Signal the next SM
  irq(rel(1))

  # Jump to the entry for this SM (preloaded in ISR)
  mov(exec, isr)

  # Fillout to 32 full opcodes so our calculated jump
  # locations are correct (never actually reached)
  mov(exec, isr)
  mov(exec, isr)

class OpcodeWriter:
  def __init__(self, sm_ids=(0, 1, 2, 3), miso_pin=23, clk_pin=24, freq=125_000_000):
    self.sms = []

    for sm_id in sm_ids:
      sm = rp2.StateMachine(
        sm_id,
        sram_write,
        freq=freq,
        out_base=Pin(miso_pin),
        in_base=Pin(clk_pin),
        jmp_pin=Pin(clk_pin),
      )
      self.sms.append(sm)

    self.reset()

  def reset(self):
    self.op_index = 0

    # Load ISR with SM specific jump opcode
    for i in range(4):
      self.sms[i].exec(f'set(x,{i*3+1})')
      self.sms[i].exec(f'mov(isr, x)')

    # Kick off SM0
    self.sms[0].exec(f"irq(0)")

    # Step 4: Reactivate all SMs
    for sm in self.sms:
      sm.active(1)

  # Distribute Opcodes across 4 SMs
  def write(self, word1, word2):
    w = ((word1 & 0xFF) << 24) | ((word1 & 0xFF00) << 8) | ((word2 & 0xFF) << 8) | ((word2 & 0xFF00) >> 8)
    self.sms[self.op_index//8].put(w)
    self.op_index += 1
    if self.op_index == 32:
      self.op_index = 0

  def stop(self):
    for sm in self.sms:
      sm.active(0)

