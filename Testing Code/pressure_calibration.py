import serial
import time
import multiprocessing as mp
from scipy.signal import butter, filtfilt
import statistics
import numpy as np
import re

MAXLEN = 150

def update_buffer(buffer, item):
    buffer.append(item)
    if len(buffer) > MAXLEN:
        buffer.pop(0)
    return buffer

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def peak_height(buffer):
    fs = 1/.041
    lowcut = 1/3  # Lower cutoff frequency
    highcut = 3.5  # Upper cutoff frequency

    # Apply bandpass filter
    filtered_data = butter_bandpass_filter(buffer, lowcut, highcut, fs, order=6)
    max_i = []
    wlen = 15
    i = 0
    while i < len(filtered_data)-wlen:
        mid_i = (wlen-1)/2
        temp_win = []
        for j in range(wlen):
            temp_win.append(filtered_data[i+j])
        if (np.argmax(temp_win) == mid_i) & ((max(temp_win) - min(temp_win)) > .4):
            max_i.append(int(i+mid_i))
        i += 1

    peaks = []

    for j in range(len(max_i)-1):
        temp_min = min(filtered_data[max_i[j]:max_i[j+1]])
        diff = ((filtered_data[max_i[j]] + filtered_data[max_i[j+1]])/2) - temp_min
        if diff < 10:
            peaks.append(diff)
    
    if len(peaks) == 0:
        return -(max(filtered_data) - min(filtered_data))
    else:
        return statistics.mean(peaks)

def serial_data(buffer_data, buffer_data_raw, con, btn_state):
    # Open the serial port
    port_name = 'COM5'  # Adjust this based on your system
    ser = serial.Serial(port_name, baudrate=115200, timeout=1)
    #time.sleep(3)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    pattern = r'^-?\d+(\.\d+)?,-?\d+(\.\d+)?,-?\d+(\.\d+)?$'
    time1 = time.time()
    time_array = []
    while True:
        data = ser.readline().decode().strip()
        if re.match(pattern, data):
            data_list = data.split(",")
            #print(f'Received: {data_list[1]}')
            buffer_data = update_buffer(buffer_data, float(data_list[1]))
            buffer_data_raw = update_buffer(buffer_data_raw, float(data_list[0]))
            btn_state.value = int(data_list[2])
        ser.write((str(con.value)+"\n").encode())

def tcontrol(buffer_data, buffer_data_raw, con, btn_state):
    temp_time = -1
    start = 1
    mode = 0
    count = 0
    avg_sp = 45
    avg_array = []
    total_avg = []
    #tests = [203, 87, 127, 167, 207] # [48, 87, 127, 167]
    tests = [40, 80, 120, 160, 200]
    for test in tests:
        count = 0
        avg_array = []
        while count < 5:
            #print(mode)
            #print(f'buttn: {btn_state.value}')
            if len(buffer_data) >= 3:
                avg = statistics.mean(buffer_data[-10:])
                avg_raw = statistics.mean(buffer_data_raw[-3:])
            if (btn_state.value == 1) & ((temp_time == -1) | (time.time()-temp_time > 1)):
                mode = 0
                avg_array.append(avg_raw)
                count += 1
                temp_time = time.time()
            if len(buffer_data) > 50:
                if mode == 0:
                    con.value = 1100
                    if avg >= test:
                        mode = 1
                elif mode == 1:
                    con.value = 1010
            if count >= 5:
                con.value = 1000
                temp_avg = statistics.mean(avg_array)
        total_avg.append(temp_avg)
    con.value = 1011
    print(total_avg)

if __name__ == "__main__":
    manager = mp.Manager()
    buffer_data = manager.list()
    buffer_data_raw = manager.list()
    btn_state = mp.Value('i', 0)
    con = mp.Value('i', 1000)
    serial_process = mp.Process(target=serial_data, args=(buffer_data, buffer_data_raw, con, btn_state, ))
    control_process = mp.Process(target=tcontrol, args=(buffer_data, buffer_data_raw, con, btn_state, ))


    serial_process.start()
    control_process.start()

    try:
        serial_process.join()
        control_process.join()
    except KeyboardInterrupt:
        print("Processes Joined")
        serial_process.join()
        control_process.join()