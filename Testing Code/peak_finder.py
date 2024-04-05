import csv
from scipy.fft import rfft, rfftfreq, irfft
import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import butter, filtfilt

data = []

with open('testData1.csv', newline='') as file:
    reader = csv.reader(file)
    for row in reader:
        data.append(float(row[0]))

#bf = data[564:764]
#nbf = data[1455:1655]
bf = data[564:1300]
nbf = data[1455:2579]
win = data[564:2579]

fs = 1/.041
N = len(win)
yf = rfft(win)
xf = rfftfreq(N, 1 / fs)[:N//2]
points_per_freq = len(xf) / (fs / 2)
target_id1 = int(points_per_freq * 1/4)
target_id2 = int(points_per_freq  * 3.5)
yf[0:target_id1] = 0
yf[target_id2:-1] = 0
hr = xf[np.argmax(2.0/N * np.abs(yf[0:N//2]))] #Hz
#print(hr)
#print(1/(hr/.041))

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

# Sample rate and desired cutoff frequencies (in Hz)
lowcut = 1/3  # Lower cutoff frequency
highcut = 3.5  # Upper cutoff frequency

# Apply bandpass filter
filtered_data = butter_bandpass_filter(win, lowcut, highcut, fs, order=6)

max_i = []
min_i = []
wlen = 15
i = 0
while i < len(filtered_data)-wlen:
    mid_i = (wlen-1)/2
    temp_win = []
    for j in range(wlen):
        temp_win.append(filtered_data[i+j])
    if (np.argmax(temp_win) == mid_i) & ((max(temp_win) - min(temp_win)) > .4):
        max_i.append(int(i+mid_i))
    elif (np.argmin(temp_win) == mid_i) & ((max(temp_win) - min(temp_win)) > .3):
        min_i.append(int(i+mid_i))
    i += 1

peaks = []

for j in range(len(max_i)-1):
    temp_min = min(filtered_data[max_i[j]:max_i[j+1]])
    diff = ((filtered_data[max_i[j]] + filtered_data[max_i[j+1]])/2) - temp_min
    if diff < 10:
        peaks.append(diff)
print(np.mean(peaks))

max_i_data = [filtered_data[i] for i in max_i]
min_i_data = [filtered_data[i] for i in min_i]

plt.figure()
plt.plot(win, 'b-', label='Original Data')
plt.xlabel('Samples')
plt.ylabel('Pressure [mmHg]')
plt.title('Unfiltered Data')
plt.figure()
plt.plot(filtered_data, 'r-', linewidth=2, label='Filtered Data')
plt.scatter(max_i, max_i_data, color='green', label='Peak Max')
#plt.scatter(min_i, min_i_data, color='black', label='Min')
plt.xlabel('Samples')
plt.ylabel('Pressure [mmHg]')
plt.title('Filtered Data')
plt.legend()
plt.grid(True)
plt.show()