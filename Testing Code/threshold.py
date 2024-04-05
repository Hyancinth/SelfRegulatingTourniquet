import serial
import time
import multiprocessing as mp
from scipy.signal import butter, filtfilt
import statistics
import numpy as np

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

def serial_data(buffer_data, con, btn_state):
    # Open the serial port
    port_name = 'COM5'  # Adjust this based on your system
    ser = serial.Serial(port_name, baudrate=115200, timeout=1)
    time.sleep(3)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time1 = time.time()
    time_array = []
    while True:
        data = ser.readline().decode().strip()
        if data:
            data_list = data.split(",")
            #print(f'Received: {data_list[1]}')
            buffer_data = update_buffer(buffer_data, float(data_list[1]))
            btn_state.value = int(data_list[2])
        ser.write((str(con.value)+"\n").encode())

def tcontrol(buffer_data, con, btn_state):
    temp_time = -1
    start = 1
    mode = 0
    count = 0
    avg_sp = 130
    peak_array = []
    while True:
        #print(mode)
        #print(f'buttn: {btn_state.value}')
        if (btn_state.value == 1) & ((temp_time == -1) | (time.time()-temp_time > 1)):
            mode = 0
            peak_array.append(peak_height(buffer_data))
            count += 1
            avg_sp = statistics.mean(buffer_data) + 10
            temp_time = time.time()
        if len(buffer_data) > 50:
            avg = statistics.mean(buffer_data)
            if mode == 0:
                con.value = 1100
                if avg >= avg_sp:
                    mode = 1
            elif mode == 1:
                con.value = 1010
        if count >= 10:
            con.value = 1011
            peak_avg = np.mean(peak_array)
            print(f'peak avg: {peak_avg}')
            print(peak_array)
            break
        time.sleep(.1)
if __name__ == "__main__":
    manager = mp.Manager()
    buffer_data = manager.list()
    btn_state = mp.Value('i', 0)
    con = mp.Value('i', 1000)
    serial_process = mp.Process(target=serial_data, args=(buffer_data, con, btn_state, ))
    control_process = mp.Process(target=tcontrol, args=(buffer_data, con, btn_state, ))


    serial_process.start()
    control_process.start()

    try:
        serial_process.join()
        control_process.join()
    except KeyboardInterrupt:
        print("Processes Joined")
        serial_process.join()
        control_process.join()

#Trial 1 - David
#1.4117705027363812, 1.2812608842404924, 1.3016410112672014, 1.4148869685089598, 1.3179992267812235, 1.2808200722651284, 1.3141376905874846, 1.448913993260597, 1.35534034890245, 1.7223273480988113

#Trial 1 - Reid
#1.8335754367683106, 1.5065798385334566, 1.3994702430251666, 1.459534299380675, 1.2529692184878387, 1.1372430495580306, 1.1097155575399316, 1.2104199129222624, 1.124673794538734, 1.1978277473448422
# Beginning ones a bit scuffed
        
#trial 2 David
#1.155930488266943, 1.1539952068519421, 1.0978174584736056, 1.12202187196343, 1.1073594573318168, 1.1747006574999137, 1.2731259140661773, 1.1897779506434518, 0.9198480711221719, 0.9241852776278987