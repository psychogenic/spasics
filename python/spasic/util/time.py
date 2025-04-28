'''
@author: Pat Deegan
@copyright: Copyright (C) 2025 Pat Deegan, https://psychogenic.com
'''
import machine

def set_datetime(year, month, month_day, week_day, hour, minute, sec, ms:int=0):
    setup_0 = year << 12 | month << 8 | month_day
    setup_1 = (week_day % 7) << 24 | hour << 16 | minute << 8 | sec
    machine.mem32[0x4005c004] = setup_0
    machine.mem32[0x4005c008] = setup_1
    machine.mem32[0x4005c00c] |= 0x10
