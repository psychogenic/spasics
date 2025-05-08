
import time
import i2c_server
d = i2c_server.get_i2c_device()
        
def master_get():
    v = d.sim_master_data_all()
    while len(v):
        print(v)
        time.sleep(0.05)
        v = d.sim_master_data_all()
        
def master_merge_get():
    v = d.sim_master_data_all()
    allbytes = bytearray()
    while len(v):
        for bts in v:
            allbytes += bts 
        time.sleep(0.05)
        v = d.sim_master_data_all()
        
    return allbytes
        
def simping(v:int=22):
    d.sim_data_received(bytearray([ord('P'), v, ord('P'), ord('N'), ord('G')]))
def filesize(varid:int):
    d.sim_data_received(bytearray([ord('F'), ord('S'), varid]))
    
def mkdir(varid:int):
    d.sim_data_received(bytearray([ord('F'), ord('D'), varid]))
def file_unlink(varid:int):
    d.sim_data_received(bytearray([ord('F'), ord('U'), varid]))
def file_move(srcvarid:int, destvarid:int):
    d.sim_data_received(bytearray([ord('F'), ord('M'), srcvarid, destvarid]))
    
def open_read(varid:int):
    d.sim_data_received(bytearray([ord('F'), ord('O'), varid, ord('R')]))

def file_close():
    d.sim_data_received(bytearray([ord('F') + ord('C')]))
    
def file_read(num_bytes:int=0):
    if num_bytes:
        d.sim_data_received(bytearray([ord('F') + ord('R'), num_bytes % 256]))
    else:
        d.sim_data_received(bytearray([ord('F') + ord('R')]))
        
def file_write(bts_to_write:bytearray):
    bts = bytearray([ord('F') + ord('W')])
    
    if len(bts_to_write) < 8:
        bts += bts_to_write
        d.sim_data_received(bts)
        return 
    
    bts += bts_to_write[0:8]
    i = 7
    while i < len(bts_to_write):
        end = i + 8
        if end > len(bts_to_write):
            end = len(bts_to_write) - 1
        
        bts = bytearray([ord('F') + ord('W')])
        bts += bts_to_write[i:end]
        d.sim_data_received(bts)
        time.sleep(0.02)
        i += 7
        
def open_write(varid:int):
    d.sim_data_received(bytearray([ord('F'), ord('O'), varid, ord('W')]))

def checksum(varid:int):
    d.sim_data_received(bytearray([ord('F'), ord('Z'), varid]))
def getvar(v:int):
    d.sim_data_received(bytearray([ord('V'), v]))
def setvar(v:int, val):
    if len(val) < 6:
        bts = bytearray([ord('V') + ord('S'), v])
        bts += val
        d.sim_data_received(bts)
        return 
    bts = bytearray([ord('V') + ord('S'), v])
    bts += val[0:7]
    d.sim_data_received(bts)
    time.sleep(0.02)
    i = 6
    while i < len(val):
        end = i + 6
        if end > len(val):
            end = len(val)
        
        bts = bytearray([ord('V') + ord('A'), v])
        bts += val[i:(end+1)]
        d.sim_data_received(bts)
        time.sleep(0.02)
        
        i += 6
        