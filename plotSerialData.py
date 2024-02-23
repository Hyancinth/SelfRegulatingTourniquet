# imports 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("serialData1.csv") #open csv
# serialData1 has some nice data with respect to pulses

# print(df.to_string()) 

dataCol = df.iloc[:,0] # get column of interest [count, %fullscale pressure, pressure, temperature]
# count seems to be what we want though the scale is weird 

# print(len(dataCol))


timeList = np.arange(0, len(df.index), 1) # create time list
timeList*0.41 # modify time scale to match recording frequency 

# print(timeList)
# print(len(timeList))

# plot
plt.plot(timeList, dataCol) # plot data 
plt.show()



