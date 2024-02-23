# imports
import serial
import csv

# Configure the serial port
ser = serial.Serial('COM3', 115200)  # Replace 'COM#' with the appropriate port and 115200 with the baud rate



def processingLoop(csvfile): 
    """ Read serial port 
    :param csvfile: output csv file name
    """
    # try catch
    try: 
        csv_writer = csv.writer(csvfile) # csv writer

        while True:
            # Read a line from the serial port
            line = ser.readline().decode('utf-8').strip() # of type string

            # Print the received data
            print("Received:", line)

            dataList = line.split() # splits data, interested in index 6

            print(dataList) # sometimes there will be an index out of bounds error. uncomment this line if that occurs
            csv_writer.writerow([dataList[4], dataList[5], dataList[6], dataList[7]]) # write data of interest to csv file
            csvfile.flush() # write to file in real time (else it will read to the file after the script is interrupted)

    except KeyboardInterrupt:
        # Close the serial port when the script is interrupted
        ser.close()
        csvfile.close()
        print("Serial port closed.")

# writing to csv file 
with open('serialData1.csv', 'w', newline='') as file:
    processingLoop(file)