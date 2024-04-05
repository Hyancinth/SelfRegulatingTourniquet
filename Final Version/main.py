# imports
import serial
import re
from multiprocessing import Process, Queue
from procCon import ProcCon
from GUI_GridLayout_v5 import ProcGUI

import time
import random
 
pC = ProcCon() # create an instance of ProcA

dataQueueCon = Queue() # create a queue for prsocA
dataQueueGUI = Queue() # create a queue for procA
convarQueue = Queue()
guivarrecvQueue = Queue()
guivarsendQueue = Queue()

# ~.021 sec/samples 
MAXLEN = 150

def update_buffer(buffer, item):
    buffer.append(item)
    if len(buffer) > MAXLEN:
        buffer.pop(0)
    return buffer

'''
    Main function that sends data to procA and procB
    In our case we would be reading in serial data here
'''
def main():
    pattern = r'^-?\d+(\.\d+)?,-?\d+(\.\d+)?,-?\d+(\.\d+)?$'
    port_name = 'COM5'  # Adjust this based on your system
    ser = serial.Serial(port_name, baudrate=115200, timeout=1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    buffer_data = []
    con_var = {
        "btn": 0,
        "con": 1000,
        "mode": 0,
        "temp_time": 0,
        "btn_time": -1,
        "avg_sp": 120,
        "repeat": 0,
        "peaked": 0,
        "maintain": 0,
        "duration": 2,
        "setpoint": 0,
        "time_sp": time.time()
    }
    gui_recv = -2
    gui_var_send = {
        "cuff_p": 0,
        "setpoint": -1,
    }
    pG = ProcGUI(dataQueueGUI, guivarrecvQueue, guivarsendQueue)
    pG.start()
    time_sp = time.time()
    while True:
        data = ser.readline().decode().strip()
        if re.match(pattern, data):
            data_list = data.split(",")
            print(f'Received: {data_list[1]}')
            buffer_data = update_buffer(buffer_data, float(data_list[1]))
            con_var["btn"] = int(data_list[2])
        dataQueueCon.put(buffer_data) # put data in mainQueueA
        #if time.time() - time_sp >= 1:
        #    dataQueueGUI.put(buffer_data)
        #
        print(f'con set: {con_var["setpoint"]}')
        convarQueue.put(con_var)
        pC.procCon(dataQueueCon, convarQueue, guivarsendQueue) # send data to procA
        #pG.procGUI(dataQueueGUI, guivarrecvQueue, guivarsendQueue) # send data to procB
        #if not convarQueue.empty():
        #    con_var = convarQueue.get(block = False)
        con_var = convarQueue.get()
        if not guivarrecvQueue.empty():
            gui_recv = guivarrecvQueue.get(block = False)
            if gui_recv >= 0:
                print("setpoint")
                con_var["setpoint"] = gui_recv
                print(con_var["setpoint"])

        if (gui_recv >= -1):
            #print(con_var["con"])
            ser.write((str(con_var["con"])[0:4]+"\n").encode())
        elif gui_recv == -2:
            ser.write((str(1011)+"\n").encode())
        #print(gui_recv)
        #print(gui_var_send)
        #ser.write((str(con_var["con"])+"\n").encode())
if __name__ == "__main__":
    
    # optional stuff? 
    # mainProc = Process(target=main) # create a process
    # mainProc.daemon = True # set the process as a daemon
    # mainProc.start() # start the process
    # mainProc.join() # join the process
    
    main()

"""
Control Flow:
setpoint = 120 mmHg
0. Inflate to setpoint -> goto 2.
    1100
1. Measure peak
    Higher than threshold-> setpoint + 20, goto 1.
    Lower than threshold -> goto 3.
    1000
2. Open slow release valve and measure peak
    Higher than threshold -> goto 4.
    1010
3. Inflate to currentPressure + 5, goto 5.
    1100
4. Measure peak
    Higher than threshold-> goto 4.
    1000
5. Safety - open valves turn off motor
    1011

"""