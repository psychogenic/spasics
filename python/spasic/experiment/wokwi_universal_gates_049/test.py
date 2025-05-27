import time
from spasic.experiment.experiment_result import ExpResult
from spasic.experiment.experiment_parameters import ExperimentParameters

def nand(a, b):
    return (a&b)^1

def u21(a, b, c, d):
    return (a&~b)^c^d

def u31(a, b, c, d, e, f):
    return (((a^~b)&c)|(d^e))^((d|~a)&b)^f

def u22(a, b, c, d, e, f):
    return ((((a&~b)^c^d)&(c|e|a))^((b^a^f)|(d&~c)),
            (((a&~b)^c^d)&(c|e|~a))^((b^a)|(d&~c)|e))

def u41(a, b, c, d, e, f, g, h, i, j):
    return (((((a|b)&(c|~d))^(e&f)^(g&h))&(((f^d)|(i^~h))^(g|b)^(~h|b)))^
            ((((e|~g)^j^f)&(e|~g)&(e^~b))|((a^b)&~j&~c)|(j&~i)|h|d)^
            ((((a^d)&c&~f)^(e|~g)^(h&~b))&((a&~b)|j|g)&(g|f)&~e&i)^
            (((j&~g)|(a^~b))&((i&d)|~a|~f))^((~c|i)&(i|b))^((j|f)&~h&a))

def ref(hi, lo):
    a, b, c, d, e, f, g, h = lo & 1, lo>>1 & 1, lo>>2 & 1, lo>>3 & 1, lo>>4 & 1, lo>>5 & 1, lo>>6 & 1, lo>>7 & 1
    i, j, k, l, m, n, o, p = hi & 1, hi>>1 & 1, hi>>2 & 1, hi>>3 & 1, hi>>4 & 1, hi>>5 & 1, hi>>6 & 1, hi>>7 & 1
    q = u21(a, b, c, d)
    r = u31(a, b, c, d, e, f)
    s, t = u22(a, b, c, d, e, f)
    u = u41(a, b, c, d, e, f, g, h, i, j)
    v = nand(e, f)
    w = u21(g, h, i, j)
    x = u31(k, l, m, n, o, p)
    out = q | r<<1 | s<<2 | t<<3 | u<<4 | v<<5 | w<<6 | x<<7
    return out

def run_test(params:ExperimentParameters, response:ExpResult, num_iterations:int=255, mask:int=255):
    response.result = bytearray(10)

    tt = params.tt
    tt.shuttle.wokwi_universal_gates_049.enable()
    tt.clock_project_stop()
    tt.uio_oe_pico.value = 255  # bidirs are outputs for pico, inputs for asic

    ok_count = 0
    for it in range(num_iterations):
        response.result[0] = it
        first_error = True
        for hi in range(256):
            tt.uio_in.value = hi
            response.result[1] = hi
            for lo in range(256):
                
                if not params.keep_running:
                    # We've been asked to terminate. Indicate reason in results array
                    response.result[0:4] = b'TERM'
                    return
                tt.ui_in.value = lo
                response.result[2] = lo
                rout = ref(hi, lo)
                out = tt.uo_out.value
                ok = out & mask == rout & mask
                if ok:
                    ok_count += 1
                    response.result[3] = ok_count>>16 & 255
                    response.result[4] = ok_count>>8 & 255
                    response.result[5] = ok_count & 255
                else:
                    if first_error:
                        response.result[6] = hi
                        response.result[7] = lo
                        first_error = False
                    response.result[8] = hi
                    response.result[9] = lo
