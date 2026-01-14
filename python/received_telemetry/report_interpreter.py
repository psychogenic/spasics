'''
Created on Jan 8, 2026

Experiment-specific parser functions for results collected in ResponseStatus and ResponseExperiment packets.

To interpret results, just 

  1) edit the resultparse_* function for your specific experiment
  2) return a string based on the contents of the result:bytearray param
  3) the end
  
@see: the resultparse_tt_um_oscillating_bones and resultparse_rp2_temperature for examples

@author: Pat Deegan
@copyright: Copyright (C) 2026 Pat Deegan, https://psychogenic.com
'''

def resultparse_default(result:bytearray) -> str:
    return str(result)
    

def resultparse_tt_um_oscillating_bones(result:bytearray) -> str:
    #return resultparse_default(result)
    if len(result) < 4:
        return f'Weird, not enough bytes in {result}'
    
    return f'loop {result[0]} avg {int.from_bytes(result[1:4], "little")}'


def resultparse_rp2_temperature(result:bytearray) -> str:
    def reading_to_temp(start:int, end:int):
        v = int.from_bytes(result[start:end], 'little')
        voltage = v * 3.3/(2**16 - 1)
        temp = 27 - (voltage - 0.706) / 0.001721  
        return f'{temp:.2f}'

    if len(result) < 2:
        return b'Not enough bytes {result}'
    
    parsed = f"cur {reading_to_temp(0,2)} "
    
    if len(result) < 4:
        return parsed
    
    parsed += f"max {reading_to_temp(2,4)} "
    
    if len(result) < 6:
        return parsed
    
    parsed += f"min {reading_to_temp(4,6)} "
    if len(result) < 8:
        return parsed
    
    parsed += f"avg {reading_to_temp(6,8)} "
    if len(result) < 10:
        return parsed
    
    parsed += f"readings {int.from_bytes(result[8:10], 'little') * 10} "
    
    return parsed




def resultparse_tt_um_test(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_fstolzcode(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_qubitbytes_alive(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_urish_spell(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_wokwi_universal_gates_049(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_andrewtron3000(result:bytearray) -> str:
    return resultparse_default(result)


def resultparse_tt_um_MichaelBell_tinyQV(result:bytearray) -> str:
    # Status is the same from all programs, but may not be present
    status = ""
    if len(result) > 9:
        if result[9] < 4:
            decoded_status = ["INVALID", "STARTED", "ABORTED", "FINISHED"][result[9]]
        else:
            decoded_status = f"{result[9]}??"
        status = f"status: {decoded_status}  "
    
    parsed = f"TinyQV {status}Data: {result[0:8].hex()}\n"

    # Simple program result is uo_out, bytes_written, loops run
    uo_out = result[0]
    bytes_written = int.from_bytes(result[1:5], 'little')
    loops = int.from_bytes(result[5:9], 'little')
    parsed += f"  Simple: Out: {uo_out:02x}   Bytes written: {bytes_written}  Loops: {loops}\n"

    # Prime test result
    val = 0
    for i in range(5):
        if result[i] == 0xff:
            for j in range(4):
                val += result[(i+1+j)%5] << (j*7)
            break
    status = "Invalid"
    if val != 0:
        if val == 0x204081:
            status = "PRIME"
        else:
            status = f"Factor: {val}"
    addr = result[5]
    loops = int.from_bytes(result[6:9], 'little')
    parsed += f"  Prime:  {status}  Addr: {addr:02x}  Loops: {loops}"

    return parsed

def resultparse_tt_um_lisa(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_ttrpg_dice(result:bytearray) -> str:
    return resultparse_default(result)
def resultparse_tt_um_cejmu(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_msg_in_a_bottle(result:bytearray) -> str:
    return resultparse_default(result)


def resultparse_tt_um_CKPope_top(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_PAL(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_dlmiles_muldiv8(result:bytearray) -> str:
    return resultparse_default(result)
def resultparse_tt_um_dlmiles_muldiv8_sky130faha(result:bytearray) -> str:
    return resultparse_default(result)

def resultparse_tt_um_ttrpg_SEU(result:bytearray) -> str:
    return resultparse_default(result)
def resultparse_tt_contributors(result:bytearray) -> str:
    return result.decode('ascii')

def resultparse_tt_test_experiment(result:bytearray) -> str:
    return resultparse_default(result)
def resultparse_tt_um_factory_test(result:bytearray) -> str:
    return resultparse_default(result)


ResultParserMap = {
    1:  resultparse_tt_um_test,
    2:  resultparse_tt_um_fstolzcode,
    3:  resultparse_tt_um_oscillating_bones, # non-terminating, explicit abort required
    4:  resultparse_tt_um_qubitbytes_alive,
    5:  resultparse_tt_um_urish_spell,
    6:  resultparse_wokwi_universal_gates_049,
    7:  resultparse_tt_um_andrewtron3000,
    8:  resultparse_tt_um_MichaelBell_tinyQV,
    9:  resultparse_tt_um_lisa,
    10: resultparse_tt_um_ttrpg_dice,
    11: resultparse_tt_um_msg_in_a_bottle,
    12: resultparse_tt_um_cejmu,
    13: resultparse_rp2_temperature,
    14: resultparse_tt_um_CKPope_top,
    15: resultparse_tt_um_PAL,
    16: resultparse_tt_um_dlmiles_muldiv8,
    17: resultparse_tt_um_dlmiles_muldiv8_sky130faha,
    18: resultparse_tt_um_ttrpg_SEU,
    
    0x80: resultparse_tt_contributors,
    0x81: resultparse_tt_test_experiment,
    0x82: resultparse_tt_um_factory_test,
    0x83: resultparse_tt_test_experiment
    
}


StatusResultParserMap = {
}


