import time
import statistics
from scipy.signal import butter, filtfilt
import numpy as np
'''
    Analagous to the controller
'''

TH = 1.2

class ProcCon:
    def procCon(self, dataQueue, convarQueue, guivarQueue): # receive data from main
        print("procCon Here")
        try:
            if(dataQueue.empty() == False) | (convarQueue.empty() == False): # check if the queue is not empty
                print("procCon Here2")
                data = dataQueue.get(block = False)
                var = convarQueue.get(block = False)
                convar = self.controller(data, var)
                var = convar[0]
                guivar = convar[1]
                if guivarQueue.empty():
                    guivarQueue.put(guivar)
                convarQueue.put(var)
        except Exception as e:
            print(e)

    def controller(self, data, var):
        #print(f'mode: {var["mode"]}')
        guivar = {
            "cuff_p": 0,
            "setpoint": -1,
        }
        if len(data) > 0:
            avg1 = statistics.mean(data)
            avg2 = statistics.mean(data[-10:])
            guivar["cuff_p"] = avg2
        if var["mode"] == 5:
            var["con"] = 1011
        else:
            if var["setpoint"] > 0:
                print("setpoint con")
                if var["mode"] < 6:
                    print("here6a")
                    var["mode"] = 6
            elif var["mode"] >= 6:
                var["mode"] = 0

            if (len(data) >= 25):
                if (statistics.mean(data) > 280):
                    var["con"] = 1011
                    var["mode"] = 5
            if (var["btn"] == 1) & ((var["btn_time"] == -1) | (time.time()-var["btn_time"] > 1)):
                var["btn_time"] = time.time()
                var["con"] = 1011
                var["mode"] = 5
            if var["mode"] == 0:
                print("mode0")
                var["con"] = 11000
                if len(data) >= 25:
                    #print(f'Control: {var["con"]} {avg}')
                    if avg2 >= var["avg_sp"]:
                        var["mode"] = 1
                        var["temp_time"] = time.time()
                        var["duration"] = 5
            elif var["mode"] == 1:
                print("mode1")
                var["con"] = 10001
                if (len(data) >= 50) & ((time.time() - var["temp_time"]) > var["duration"]):
                    var["duration"] = 3
                    peak = self.peak_height(data)
                    if peak > TH:
                        var["mode"] = 0
                        var["avg_sp"] = avg1 + 20
                    elif peak < 0:
                        if abs(peak) > .1:
                            var["repeat"] = 0
                            var["mode"] = 2
                            var["temp_time"] = time.time()
                        elif var["repeat"] < 10:
                            var["repeat"] += 1
                        else:
                            var["con"] = 1011
                            var["mode"] = 5
                    else:
                        var["mode"] = 2
                        var["temp_time"] = time.time()
            elif var["mode"] == 2:
                print("mode2")
                var["con"] = 10102
                peak = self.peak_height(data)
                if peak > TH:
                    var["mode"] = 3
                    var["avg_sp"] = avg2 + 5
                elif peak < 0:
                    if abs(peak) > .1:
                        var["repeat"] = 0
                    elif var["repeat"] < 10:
                        var["repeat"] += 1
                    else:
                        var["con"] = 1011
                        var["mode"] = 5
            elif var["mode"] == 3:
                var["con"] = 11003
                print("mode3")
                if avg2 >= var["avg_sp"]:
                    var["mode"] = 4
                    var["temp_time"] = time.time()
                    var["duration"] = 5
            elif var["mode"] == 4:
                var["con"] = 10004
                print("mode4")
                if (time.time() - var["temp_time"]) > var["duration"]:
                    peak = self.peak_height(data)
                    if peak > TH:
                        var["mode"] = 3
                        var["avg_sp"] = avg2 + 5
                    elif peak < 0:
                        if abs(peak) > .1:
                            var["repeat"] = 0
                        elif var["repeat"] < 10:
                            var["repeat"] += 1
                        else:
                            var["con"] = 1011
                            var["mode"] = 5
            elif var["mode"] == 5:
                print("mode5")
                var["con"] = 10115
            elif var["mode"] == 6:
                print("here6b")
                var["con"] = 10006
                if avg2 < var["setpoint"]:
                    var["mode"] = 7
                if avg2 > (var["setpoint"] + 5):
                    var["mode"] = 8
            elif var["mode"] == 7:
                print("here7")
                var["con"] = 11007
                if avg2 > (var["setpoint"] + 5):
                    var["mode"] = 6
            elif var["mode"] == 8:
                var["con"] = 10108
                if avg2 < (var["setpoint"] + 5):
                    var["con"] = 10006
                    var["mode"] = 6
        return [var, guivar]

    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = filtfilt(b, a, data)
        return y

    def peak_height(self, buffer):
        fs = 1/.021
        lowcut = 1/3  # Lower cutoff frequency
        highcut = 3.5  # Upper cutoff frequency

        # Apply bandpass filter
        filtered_data = self.butter_bandpass_filter(buffer, lowcut, highcut, fs, order=6)
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

    def controlA(self, procBQueue): # controlling procA based on procB
        print("Control A")
        try:
            if procBQueue.empty() == False:
                result = procBQueue.get(block = False)
                if result == 0:
                    print("Keep Going")
                elif result == 1:
                    print("Stop")
            else:
                print("B is empty")
            # time.sleep(1)
        except Exception as e:
            print(e)

"""
Control Flow:
setpoint = 120 mmHg
1. Inflate to setpoint -> goto 2.
    1100
2. Measure peak
    Higher than threshold-> setpoint + 20, goto 1.
    Lower than threshold -> goto 3.
    1000
3. Open slow release valve and measure peak
    Higher than threshold -> goto 4.
    1010
4. Inflate to currentPressure + 5, goto 5.
    1100
5. Measure peak
    Higher than threshold-> goto 4.
    1000
6. Safety - open valves turn off motor
    1011

"""