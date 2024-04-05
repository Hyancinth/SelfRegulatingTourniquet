from __future__ import annotations
from typing import *

import sys
import os

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout, QLCDNumber 

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import matplotlib as mpl
import numpy as np

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

#--- Global variables allow communication between classes ---#
global start_pressed, pressureData, timeData, windowSize
start_pressed = 0
pressureData = []
timeData = []
windowSize = 200

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from multiprocessing import Process, Queue
import sys

import time

#Multiprocessing class
class ProcGUI(Process):
    def __init__(self, dataQueue, GUI_var_send, GUI_var_recv):
        super().__init__()
        self.dataQueue = dataQueue
        self.GUI_var_send = GUI_var_send
        self.GUI_var_recv = GUI_var_recv

    def run(self):
        app = QApplication(sys.argv)
        window = App(self.dataQueue, self.GUI_var_send, self.GUI_var_recv)
        window.show()
        sys.exit(app.exec_())


#the App class is responsible for the main GUI window
class App(QDialog):
    def __init__(self,dataQueue, GUI_var_send, GUI_var_recv):
        super().__init__()
        self.dataQueue = dataQueue
        self.GUI_var_send = GUI_var_send
        self.GUI_var_recv = GUI_var_recv
        self.title = 'Automated Pressure Cuff GUI'
        self.left = 0
        self.top = 30
        self.width = 2500
        self.height = 1000
        self.initUI()
    
    #initUI is laying out the top level groups (adding horizontal box groups within a vertical box group)
    #which the widgets (graphs, buttons, etc) will be placed into
    def initUI(self):

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.myFig = Canvas(interval=1000)
        
        windowLayout = QGridLayout()

        # Start button configuration
        start_button = QPushButton("START",self)
        start_button.setMinimumHeight(450)
        start_button.setStyleSheet("background-color : green")
        start_button.setFont(QFont("Arial",50))
        start_button.clicked.connect(self.start_clicked)

        # Stop button configuration
        stop_button = QPushButton("STOP",self)
        stop_button.setMinimumHeight(450)
        stop_button.setStyleSheet("background-color : red")
        stop_button.setFont(QFont("Arial",50))        
        stop_button.clicked.connect(self.stop_clicked)

        # Elapsed Time configuration
        self.timed = False
        self.time_start = 0
        self.time_plt = 0
        self.time_elapsed = 0
        self.manual_value = "0"
        self.start = False
        self.timer = QTimer(self)
        self.time = QTime(0,0,0)
        self.timer.timeout.connect(self.updateGUI)
        self.timer.start(500)
        self.elapsed = QLabel("00:00:00", self)
        self.elapsed.setFont(QFont("Arial", 50))

        # Manual Override Confuguration
        manual_button = QPushButton("Set Manual Override")
        manual_button.setMinimumHeight(150)
        manual_button.setFont(QFont("Arial",20)) 
        manual_button.clicked.connect(self.manual_clicked)

        #Cuff Pressure Setpoint Configuration
        self.setpointLabel = QLabel("---", self)
        self.setpointLabel.setFont(QFont("Arial", 50))
        self.setpoint = 0
        

        #Current Cuff Pressure Configuration
        self.currentPressureLabel = QLabel("---", self)
        self.currentPressureLabel.setFont(QFont("Arial", 50))
        self.currentPressure = 0

        #Row1
        windowLayout.addWidget(self.myFig, 0, 0)
        windowLayout.addWidget(QGroupBox("Y - Cuff Pressure (mmHg), X - time (seconds)"), 0,0)
        windowLayout.addWidget(QGroupBox("Current Cuff Pressure"), 0, 1)
        windowLayout.addWidget(self.currentPressureLabel,0,1)
        windowLayout.addWidget(QGroupBox("Cuff Pressure Setpoint"), 0, 2)
        windowLayout.addWidget(self.setpointLabel,0,2)
        windowLayout.addWidget(start_button, 0, 3)
        
        #Row2
        windowLayout.addWidget(QGroupBox("PPG Reading History"), 1,0)
        windowLayout.addWidget(QGroupBox("Elapsed Time"),1,1)
        windowLayout.addWidget(self.elapsed,1,1)
        windowLayout.addWidget(QGroupBox("Manual Override"), 1, 2)
        windowLayout.addWidget(manual_button, 1,2)
        windowLayout.addWidget(stop_button, 1, 3)
        
        self.setLayout(windowLayout)
        self.show()
    
    #start: -3
    #stop: -2
    #placeholder (do nothing): -1
    #set manual override: value >= 0

    #Routine runs when start button is pressed
    def start_clicked(self):
        self.start = True
        print("Begin Inflation")
        self.GUI_var_send.put(-1)

    #routine runs when stop button is pressed
    def stop_clicked(self):
        self.start = False
        self.manual_value = "0"
        self.GUI_var_send.put(int(self.manual_value))
        print("Emergency Stop")
        self.GUI_var_send.put(-2)

    #Update Routine for GUI (other than graph) every 1 second
    def updateGUI(self):
        if self.start:
            if self.timed == False:
                self.timed = True
                self.time_start = time.time()
                self.time_plt = time.time()

            self.time_elapsed = round(time.time() - self.time_start, 1)
    
            #update time variable for plot
            timeData.append(round(time.time() - self.time_plt, 1 ))
            if (len(timeData) >= windowSize):
                timeData.pop(0)

            #update time on GUI
            if self.time_elapsed >= 1:
                self.time = self.time.addSecs(1)
                self.time_start = time.time() 

            text = ("%s" % self.time.toString("hh:mm:ss"))
            self.elapsed.setText(text)

            #Recieve data from controller
            if (self.GUI_var_recv.empty() == False):
                data = self.GUI_var_recv.get(block = False)
                if data["cuff_p"] > 0:
                    self.currentPressure = round(data["cuff_p"], 1)
                else:
                    self.currentPressure = 0
                #self.setpoint = round(data["setpoint"], 1)
                
                #update pressure data for plot
                pressureData.append(self.currentPressure)
                if (len(pressureData) >= windowSize):
                    pressureData.pop(0)

            #Update Current Pressure Label
            self.currentPressureLabel.setText(str(self.currentPressure))

            #Update Setpoint Label
            #self.setpointLabel.setText(str(self.setpoint))

            if int(self.manual_value) > 0:
                self.setpointLabel.setText(self.manual_value)
            else:
                self.setpointLabel.setText("---")
        else:
            timeData.clear()
            pressureData.clear()
            self.timed = False
            
            self.time.isNull()
            #Update Current Pressure Label
            self.currentPressure = 0
            self.currentPressureLabel.setText(str(self.currentPressure))

            #Update Setpoint Label
            #self.setpoint = 0
            #self.setpointLabel.setText(str(self.setpoint))
            self.setpointLabel.setText("---")

    #Manual Push Button Pressed Routine
    def manual_clicked(self):
        self.manual_value, done = QInputDialog.getText(self, "Pressure", "Enter Desired Cuff Pressure")

        if done:
            self.GUI_var_send.put(int(self.manual_value))
            print(f'man val {self.manual_value}')
    


#The Canvas is responsible for plotting using matplotlib        
class Canvas(FigureCanvas):
 
    def __init__(self, interval:int) -> None:
        '''
        :param x_len:       The nr of data points shown in one plot.
        :param y_range:     Range on y-axis.
        :param interval:    Get a new datapoint every .. milliseconds.

        '''
        super().__init__(mpl.figure.Figure())

        # Store two lists _x_ and _y_
        self._x_ = timeData
        self._y_ = pressureData

        # Store a figure ax
        self._ax_ = self.figure.subplots()

        # Initiate the timer
        self._timer_ = self.new_timer(interval, [(self._update_canvas_, (), {})])
        self._timer_.start()
        return

    def _update_canvas_(self) -> None:
        '''
        This function gets called regularly by the timer.

        '''
        #print(timeData)
        #print(pressureData)
        if (len(pressureData) == len(timeData)):
            self._y_ = pressureData
            self._x_ = timeData
            self._ax_.clear()                                   # Clear ax
            self._ax_.plot(self._x_, self._y_)                  # Plot y(x)
            self.draw()
        return
    
