#!   /usr/bin/env   python
#    coding: utf8
'''
The serial_bridge class allows to connect with WR devices over serial port.

@file
@author Fran Romero
@date September 17, 2015
@copyright LGPL v2.1
@ingroup bridges
'''


#------------------------------------------------------------------------------|
#                   GNU LESSER GENERAL PUBLIC LICENSE                          |
#                 ------------------------------------                         |
# This source file is free software; you can redistribute it and/or modify it  |
# under the terms of the GNU Lesser General Public License as published by the |
# Free Software Foundation; either version 2.1 of the License, or (at your     |
# option) any later version. This source is distributed in the hope that it    |
# will be useful, but WITHOUT ANY WARRANTY; without even the implied warrant   |
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser   |
# General Public License for more details. You should have received a copy of  |
# the GNU Lesser General Public License along with this  source; if not,       |
# download it from http://www.gnu.org/licenses/lgpl-2.1.html                   |
#------------------------------------------------------------------------------|

# Imports
import re
import sys
import serial
import cmd
from wx import OutBottom

from bridges.consolebridge import ConsoleBridge
from serial_linux import *
from serial_windows import *
from core.p7sException import *
from core.gendrvr import BusCritical, BusWarning

class SerialBridge(ConsoleBridge):
    '''
    Class to handle connection with WR devices through the USB port (serial).

    This class implements the interface defined in ConsoleBridge abstract class
    for devices connected on the serial port (using USB).
    '''

    # Max timeout value (in seconds)
    MAX_TIMEOUT = 5

    #Operative system
    os = sys.platform

    #Parameters required to open a port
    baudrate = None
    rdtimeout = None
    wrtimeout = None
    interchartimeout = None
    ntries = None



    def __init__(self, interface='serial', port=None, verbose=False):
        '''
        Constructor

        Args:
            interface (str) : Indicates the bus used for the connection: in this case 'serial'.
            port (str) : Port name. Examples: "/dev/tty/USB0" for Linux, and
            "COM0" for Windows.
            verbose (bool) : Enables verbose output

        Raises:
            BadInput exception if any of the input parameters are not valid.
        '''
        # Input control
        if interface != "serial":
            raise BadData(1, "serial")
        elif 'linux2' in self.os and not re.match("^/dev/ttyUSB[0-9]{1,4}$",str(port)): #if port is not a valid port name in Linux
        #elif 'linux2' in self.os and re.match('/dev/ttyUSB',str(port)) == None: #if port is not a valid port name in Linux
            raise BadData(4, port)
        elif not ('linux2' in self.os) and re.match("^COM[0-9]{1,4}$",str(port)) == None: #if port is not a valid port name in Windows
        #elif not ('linux2' in self.os) and re.match('COM',str(port)) == None: #if port is not a valid port name in Windows
            raise BadData(5, port)

        self.interface = interface
        self.port = port
        self.bus = None
        self.verbose = verbose
        if self.isOpen() == False:
            self.open()



    def open(self, ethbone_dbg=False, baudrate=115200, rdtimeout=0.2, wrtimeout=0.2, interchartimeout=0.001, ntries=2):

        '''
        Method to open a new connection with a WR device.

        Args:
            ethbone_dbg (bool) : Flag to enable verbose output for the EtherBone driver.
            baudrate (int) : Baudrate used in the WR-LEN serial port
            wrtimeout (int) : Timeout before read after writing
            interchartimeout (int) : Timeout between characters
            rdtimeout (int) : Read timeout
            ntries (int) : How many times retry a read or a write

        Raises:
            ConsoleError : When the specified device fails opening.
        '''
        self.baudrate = baudrate
        self.rdtimeout = rdtimeout
        self.wrtimeout = wrtimeout
        self.interchartimeout = interchartimeout
        self.ntries = ntries

        if 'linux2' in self.os: #if we are in Linux it call to the linux serial bridge
            self.bus = SerialLinux(verbose=self.verbose, baudrate=self.baudrate, rdtimeout=self.rdtimeout, wrtimeout=self.wrtimeout, interchartimeout=self.interchartimeout, ntries=self.ntries)
            self.bus.open(self.port)
        else:#if we are in Windows it call to the windows serial bridge
            self.bus = SerialWindows(verbose=self.verbose, baudrate=self.baudrate, rdtimeout=self.rdtimeout, wrtimeout=self.wrtimeout, interchartimeout=self.interchartimeout, ntries=self.ntries)
            self.bus.open(self.port)



    def isOpen(self):
        '''
        This method checks wheter device connection is stablished.

        Returns:
            True if open() method has previously called, False otherwise.
        '''
        return (self.bus is not None)

    def close(self):
        '''
        Method to close an existing connection with a WR device.

        Raises:
            ConsoleError : When the connection fails closing.
        '''
        try:
            self.bus.close()
        except BusCritical as e:
            raise Error(2, e.message)

    def flushInput(self):
        '''
        Method to clear read buffer of the VUART

        Use this method before calling sendCommand the first time in order to
        clear the data in the read buffer of the Virtual UART
        '''
        if self.bus is None:
            print "Error in flushInput function"
            #raise algo
        else:
            if self.verbose:
                print("Erasing old content of buffer")
            self.bus.flushInput()


    def sendCommand(self, cmd, buffered=True):
        '''
        Method to pass a command to the Device

        This method writes a command to the input and retrieves the device
        response (if buffered is true).

        Returns:
            Outputs a list of str from WR-LEN.
        '''
        out = self.bus.cmd_w(cmd, buffered)
        #print out
        return out




    @staticmethod
    def scan(bus="all", nports="50"):
        '''
        Method to scan WR devices connected to the PC through serial interface.

        Args:
            bus (str) : Not used in serial_bridge.
            subnet(str) : In this case, number of port to scan

        Returns:
            A dict where the keys are the seen before. The value is a list with
            ports/ip dirs. availables. When there're no conneted devices, an
            empty list is returned. A example:
            ["/dev/ttyUSB0", "/dev/ttyUSB1"]

        Raises:
            Error : When the specified interface could not be scanned.
        '''

        devices = []
        num_ports = int(nports)

        if sys.platform == 'linux2' :
            port_name = '/dev/ttyUSB'
        else :
            port_name = 'COM'

        for i in range(num_ports):
            try:
                port_i = port_name + str(i)

                _serial = serial.Serial(port_i, 115200, timeout=0.5)
                _serial.setWriteTimeout(0.5)
                _serial.write(chr(27))#write an ESC if gui is enabled
                time.sleep(0.01)
                _serial.write(chr(13)) #write an ENTER for cleaning the ESC command to the input buffer if gui was disabled
                time.sleep(0.01)
                _serial.write(chr(13)) #now write ENTER to receive the prompt
                time.sleep(0.01)
                ret = _serial.read(6)
                #-- if no errors
                if 'wrc#' in ret: #this is a WR device
                    devices.append(str(port_i))

                _serial.close() #close port
            except:
                pass

        return devices
