#!/usr/bin/python -d
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------------
#  HP/Agilent E4406A Span Concatenator
#  Author: Bert Zauhar, VE2ZAZ.   Web: http://ve2zaz.net
#  Version 1, April 2014
#  #This script concatenates multiple 10MHz spans of spectrum data taken from the HP E4406A VSA.
#  __      ________ ___  ______          ______             _   
#  \ \    / /  ____|__ \|___  /   /\    |___  /            | |  
#   \ \  / /| |__     ) |  / /   /  \      / /   _ __   ___| |_ 
#    \ \/ / |  __|   / /  / /   / /\ \    / /   | '_ \ / _ \ __|
#     \  /  | |____ / /_ / /__ / ____ \  / /__ _| | | |  __/ |_ 
#      \/   |______|____/_____/_/    \_\/_____(_)_| |_|\___|\__| 
#
# This software source code is published under the GNU GPLv3 license. Please refer to
# http://www.gnu.org/licenses/gpl-3.0.html for more detail on the license agreement.
# -----------------------------------------------------------------------------------

# Python library imports
import sys
import os
import time
import datetime
from PyQt4 import QtCore, QtGui
from HP_E4406_Wideband_Window import Ui_MainWindow # Window created in Qt4 designer and compiled into python using the pyuic4 utility.
from pychart import * # For plotting
import socket # neede to communicate with E4406A

# -----------------------------------------------------------------------------------
# Global variables
ip_addr = "192.168.0.2"  # the E4406A default IP address
ip_port = 5025    # the E4406A default IP port
start_freq = 10   # The default Start frequency
stop_freq = 50    # The default Stop frequency
stop_capture_flag = False     # a flag used to indicate that the capture process must be stopped


# -----------------------------------------------------------------------------------
# Window Form Class with functions
class MyForm(QtGui.QMainWindow):
   def __init__(self, parent=None):
      global ip_addr
      global ip_port      
      global start_freq
      global stop_freq
      QtGui.QWidget.__init__(self, parent)   # Defines main window
      self.ui = Ui_MainWindow()        # Defines main window
      self.ui.setupUi(self)            #   "
      self.ui.progressBar.hide()       # hide the capture progress bar
      self.ui.stop_pushButton.hide()   # hide the Stop pushbutton
      print ""
      print "----------------------------------------------------------"
      print "HP/Agilent E4406A Span Concatenator"
      print "v1 - April 2014"
      print "By Bertrand Zauhar, VE2ZAZ, ve2zaz.net"
      print "----------------------------------------------------------"
      print ""
      print "Loading Configuration file."
      try:  # Load parameters from file at startup
         saved_file = open('saved.cfg','r') # Open saved configuration file for reading
         ip_addr = saved_file.readline()[:-1] # read ip address string from config file
         ip_addr_split = ip_addr.split(".")  # split ip address string into subnets
         self.ui.ip1_lineEdit.setText(ip_addr_split[0]) # copy subnet strings to window IP fields
         self.ui.ip2_lineEdit.setText(ip_addr_split[1])  #    "
         self.ui.ip3_lineEdit.setText(ip_addr_split[2])  #    "
         self.ui.ip4_lineEdit.setText(ip_addr_split[3])  #    "
         ip_port = int(saved_file.readline()[:-1])    # read ip port string from config file
         self.ui.ip_port_lineEdit.setText(str(ip_port))   # copy ip port string to window field
         start_freq = float(saved_file.readline()[:-1])     # read start frequency string from config file and save it to its numerical variable
         self.ui.Freq_Start_lineEdit.setText(str(start_freq))  # copy the start frequency string to window field
         stop_freq = float(saved_file.readline()[:-1])      # read stop frequency string from config file and save it to its numerical variable
         self.ui.Freq_Stop_lineEdit.setText(str(stop_freq)) # copy the stop frequency string to window field
         if (saved_file.readline()[:-1] == 'checked'): self.ui.capture_average_checkBox.setChecked(True)  # read averaging checkbox string from config file and transfer the right state to the window checkbox
         else: self.ui.capture_average_checkBox.setChecked(False)
         if (saved_file.readline()[:-1] == 'checked'): self.ui.single_graph_checkBox.setChecked(True) # read single graph checkbox string from config file and transfer the right state to the window checkbox
         else: self.ui.single_graph_checkBox.setChecked(False)
         if (saved_file.readline()[:-1] == 'checked'): self.ui.save_data_checkBox.setChecked(True)    # read save data checkbox string from config file and transfer the right state to the window checkbox
         else: self.ui.save_data_checkBox.setChecked(False)
         saved_file.close() # close config file
      except IOError: # Case where parameters retrieval from config file fails
         pass     # do nothing
      QtCore.QObject.connect(self.ui.execute_pushButton, QtCore.SIGNAL("clicked()"), self.execute_plot_captures) # the trigger for the measurement start is generated here when the button is pressed. 
      QtCore.QObject.connect(self.ui.stop_pushButton, QtCore.SIGNAL("clicked()"), self.stop_plot_captures) # the trigger for the measurement stop is generated here when the button is pressed. 
      app.aboutToQuit.connect(self.myExitHandler) # myExitHandler is a callable function executed when the script terminates.
      
   # This function executes when the user closes the main window. This saves the parameters in the config file.
   def myExitHandler(self):   
      global ip_addr
      global ip_port            
      global start_freq
      global stop_freq
      print 'Exiting. Saving Configuration file.'
      try:  # Save parameters to the config file.
         saved_file = open('./saved.cfg','w') # Open saved configuration file for writing
         saved_file.write(ip_addr + '\n')      # save ip address string
         saved_file.write(str(ip_port) + '\n')  # save ip port string
         saved_file.write(str(start_freq) + '\n')  # Save start frequency string
         saved_file.write(str(stop_freq) + '\n')   # Save stop frequency string
         if (self.ui.capture_average_checkBox.isChecked()): saved_file.write('checked\n')    # Save averaging checkbox string value
         else: saved_file.write('unchecked\n')
         if (self.ui.single_graph_checkBox.isChecked()): saved_file.write('checked\n')    # Save single graph checkbox string value
         else: saved_file.write('unchecked\n')
         if (self.ui.save_data_checkBox.isChecked()): saved_file.write('checked\n')    # Save save data checkbox string value
         else: saved_file.write('unchecked\n')
         saved_file.close() # close config file
      except IOError: # Case where parameters retrieval fails
         pass     # do nothing


   def execute_plot_captures(self):
      global QtGui
      global ip_addr
      global ip_port            
      global start_freq
      global stop_freq
      global stop_capture_flag
      self.ui.progressBar.show()    # Show progress bar
      self.ui.stop_pushButton.show()      # show stop pushbutton
      self.ui.execute_pushButton.hide()   # hide Execute pushbutton
      app.processEvents() # Refresh the window with the new values
      ip_addr = self.ui.ip1_lineEdit.text() + '.' + self.ui.ip2_lineEdit.text() + '.' + self.ui.ip3_lineEdit.text() + '.' + self.ui.ip4_lineEdit.text() # create IP address with subnet text boxes
      ip_port = int(self.ui.ip_port_lineEdit.text())  # create IP port with port textbox
      hpe4406a = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # Create the IP socket
      hpe4406a.connect((ip_addr,ip_port))    # connect to E4406A
      hpe4406a.send(":READ:SPECtrum1?\n")    # issue the command to read back the spectrum status results to extract the number of points per span
      line = hpe4406a.recv(500)     # read back the spectrum status results
      line = line.split(',')     # split the status line in its separate fields.
      num_points = int(line[2])  # third field contains the number of points per span, save that value
      print "Number of points per span: " + str(num_points)    # print the number of points
      points_step = float(line[4])/1E6    # fifth field contains the frequency step between two points, save that value 
      hpe4406a.send(":DISPlay:SPECtrum1:WINDow1:TRACe:Y1:PDIVision?\n") # Issue the command to return the Y axis reference value in dBm
      db_per_div = float(hpe4406a.recv(500))    # read back the Y axis reference value in dBm and save it.
      hpe4406a.send(":DISPlay:SPECtrum1:WINDow1:TRACe:Y1:RLEVel?\n") # Issue the command to return the Y axis reference value in dBm
      db_ref_value = float(hpe4406a.recv(500))  # read back the Y axis reference value in dBm and save it.
      start_freq = float(self.ui.Freq_Start_lineEdit.text())   # Read back the start frequency from the Start Freq textbox and save it
      stop_freq =  float(self.ui.Freq_Stop_lineEdit.text())    # Read back the stop frequency from the Stop Freq textbox and save it
      total_num_scans = max(1,round((stop_freq - start_freq)/10))    # calculate the number of 10MHz spans required to cover the frequency range and save it
      print "Scale/Div: " + str(db_per_div)     # Print the various calculated values
      print "Ref Value: " + str(db_ref_value)   #   "
      print "Start Freq: " + str(start_freq)    #   "
      print "Stop Freq: " + str(stop_freq)      #   "
      print "Number of spans to scan: " + str(total_num_scans) + "\r\n"    #   "
      if (self.ui.single_graph_checkBox.isChecked()):  # is data compression onto a single span requested via the checkbox?          
         compression_factor = total_num_scans      # yes, set the compression factor equivalent to the number of spans.
      else:                        
         compression_factor = 1     #  no, set the compression factor to 1
      scan_number = 0      # initialize the scan number counter
      line_nums = []       # initialize the data line
         # The measurement loop starts here
      while (scan_number < total_num_scans) and not(stop_capture_flag): #  if the number of scans required is not reached and if button is not pressed down stop
         if (total_num_scans > 1):  # if the total number of spans required to cover the frequency range is more than one
            span = 10      #  The span must be 10 MHz
            hpe4406a.send(":SENSe:SPECtrum:FREQuency:SPAN 10MHZ\n")    # set the E4406A to a span of 10 MHz
         else:                               # otherwise
            span = stop_freq - start_freq       # the span equals the frequency range
            hpe4406a.send(":SENSe:SPECtrum:FREQuency:SPAN " + str(span) + "MHZ\n")  # send the required span to the E4406A
         print "Capture Span #" + str(scan_number + 1)   # print the span number
         print "Span: " + str(span) + " MHz"             # print the span in MHz
         center_freq = start_freq + 0.5*span + scan_number*span   # calculate the center frequency
         print "Center Freq: " + str(center_freq) + " MHz\r\n"    # print the center frequency
         hpe4406a.send(":SENSe:FREQuency:CENTer " + str(center_freq) + "MHZ\n")     # send the center frequency to the E4406A
         if (self.ui.capture_average_checkBox.isChecked()):    # if the average data is requested by the user
            hpe4406a.send(":READ:SPECtrum7?\n")  # send the command to request the averaged spectrum data to be placed into the output buffer of the E4406A 
         else:
            hpe4406a.send(":READ:SPECtrum4?\n")  # send the command to request the spectrum data to be placed into the output buffer of the E4406A 
         num_chars = num_points *  17     # calculate the number of characters to read as a function of number of points and number of characters for each point
         line = ""   # initialize the data line
         recv_str = " "    # Initialize the receive character
         while len(line) < num_chars:     # while all characters are not read
            recv_str = hpe4406a.recv(1)   # read back one character from the E4406A
            line = line + recv_str     # add it to the received string
         line = line.split(',')     # split the received data line into a series of data points
         for i in range(0,num_points):    # loop for as many times as there are data points in the span
            line_nums.extend([(center_freq - (0.5*span) + (i*points_step),round(float(line[i]),2))]) # add the received span points to the data series as tuples
         scan_number = scan_number + 1    # the span scan is over, increase the scan value by one
         self.ui.progressBar.setValue(scan_number / total_num_scans * 100)    # Update the progress bar as a function of the total number of spans required
         app.processEvents() # Refresh the window with the new values
      del hpe4406a   # delete the socket
      # Save data to file
      if (self.ui.save_data_checkBox.isChecked()):   # if data file is to be created
         filename = ""     # initialize the data file name
         filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Data file name or Cancel', './')  # Extract the data file name from a standard file dialog
         if filename <> "":   # if a file name has been provided
            file = open(filename,'w') # Open text file for writing
            for i in range(0,len(line_nums)):      # loop for as many times as there are data points to save
               file.write(str(line_nums[i]) + "\n") # write data point to file
            file.close() # Close file
            print "Data file " + filename + " created."     # print that the data file has been created
      # Plot .pdf file
      date_and_time = datetime.datetime.now().strftime('%d%m%Y_%H%M%S')    # extract and formart the date and time 
      file_name = 'spectrum_plot_' + date_and_time + '.png'    # constitute the plot file name
      can = canvas.init(file_name)   # initialize the canvas
      theme.get_options()                 # Set the theme parameters to be appropriate to our plotting exercise
      theme.scale_factor = 3              #   "
      theme.default_line_width = 0.001    #   "
      theme.reinitialize()                # Re-initialize the theme. Must be called so that the above variables get updated
      xaxis = axis.X(format="/hC%3f", tic_interval = (span/2) * compression_factor, tic_len = 10, label="Frequency (MHz)")    # Format the X axis
      yaxis = axis.Y(tic_interval = db_per_div, label="Amplitude (dBm)")      # format the Y axis
      ar = area.T(x_axis=xaxis, x_range=(start_freq, stop_freq),     # Format the plotting area
                  x_grid_style = line_style.gray70, x_grid_interval = (span/10) * compression_factor, 
                  y_axis=yaxis, y_range=((db_ref_value - 10 * db_per_div),db_ref_value), y_grid_interval=db_per_div, 
                  y_grid_style = line_style.gray70, size=(400 * total_num_scans / compression_factor,400), legend=None)
      ar.add_plot(line_plot.T(data=line_nums, ycol=1))      # add the plot to the canvas
      ar.draw()                                             #   "
      can.close()                                           # close the canvas
         # display the .PNG plot file into the window.
      spectrum_plot = QtGui.QPixmap(file_name)  # assign the proper .PNG file name (just created plot)              
      self.ui.output_plot_label.setPixmap(spectrum_plot)    # show the .PNG file into the pre-defined label widget
      self.ui.output_plot_label.show()    # show the plot label
      self.ui.progressBar.hide()          # hide the progress bar
      self.ui.stop_pushButton.hide()      # hide the Stop pushbutton
      self.ui.execute_pushButton.show()   # Show the Execute pushbutton
      stop_capture_flag = False           # Clear the Stop process flag
      self.ui.file_result_label.setText("Image file " + file_name + " created in current directory")  # print the file name message below the image
      app.processEvents() # Refresh the window with the new values
      print "Image file " + file_name + " created in current directory"  # print the file name at the console
      print "Script completed\r\n"     # print that the script has completed the scan

   # this function sets the Stop flag when the Stop pushbutton is pressed
   def stop_plot_captures(self):
      global stop_capture_flag      
      stop_capture_flag = True      # set the Stop flag to true

# Main script definition, not to be changed
if __name__ == "__main__":
   app = QtGui.QApplication(sys.argv)
   myapp = MyForm()
   myapp.show()
   sys.exit(app.exec_())

