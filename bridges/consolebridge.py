#!   /usr/bin/env   python
#    coding: utf8
'''
ConsoleBridge abstract class

@file
@author Felipe Torres
@date August 24, 2015
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

# System imports
import abc
import sys
import serial
import time
from subprocess import check_output

# User defined imports
from core.p7sException import p7sException
from ethbone import EthBone


class ConsoleBridge():


    # Device ID for SPEC board (only one with PCI interface)
    PCI_DEVICE_ID_SPEC = 0x018d
    # Vendor ID for CERN
    VENDOR_ID_CERN = 0xce42
    # Vendor ID for SevenSolutions
    VENDOR_ID_7SOLS = 0x7501
    # WR-Periph-UART
    WR_UART_ID = 0xe2d13d04

    # Virtual UART register config
    VUART_TX_REG = 0x10
    VUART_RX_REG = 0x14
    VUART_RDY_MSK = 0x100
    VUART_RX_CNT_MSK = 0x1FFFE00
    VUART_RX_DAT_MKS = 0xFF
    VUART_OFFSET = None
    # Regular expression for a valid ip/mask
    valid_ip = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    # Regular expression for a valid pci port
    valid_pciport = r"\d{2}:\d{2}\.\d$"

    # Max timeout value (in seconds)
    MAX_TIMEOUT = 5

    '''
    Abstract class that defines the methods that must be implemented in order to connect to the console of a WR device.

    Attributes:
        port (str) : Port used for the connection
        interface (str) : Interface used for the connection
    '''

    @abc.abstractmethod
    def open(self) :
        '''
        Method to open a new connection with a WR device.

        Raises:
            ConsoleError : When the specified device fails opening.
        '''

    @abc.abstractmethod
    def close(self) :
        '''
        Method to close an existing connection with a WR device.

        Raises:
            ConsoleError : When the connection fails closing.
        '''

    @abc.abstractmethod
    def setCommand(self, cmd) :
        '''
        Method to pass a command to a WR device

        This method writes a command to the input and retrieves the device
        response (if any).

        Args:
            cmd (str) : Command

        Returns:
            A string with the device's response. A empty string is returned when
            there isn't response from device.

        Raises:
            CmdNotValid : When the passed command is not accepted by the device.
            ConsoleError : When an error was occured while reading/writing.
        '''

    @abc.abstractmethod
    def isOpen(self) :
        '''
        This method checks wheter device connection is stablished.

        Returns:
            True if open() method has previously called, False otherwise.
        '''

    @staticmethod
    def scan(bus, subnet, numport='50') :
        '''
        Method to scan WR devices connected to the PC.

        This method look for devices connected through the following interfaces:
        · Serial interface
        · PCIe bus.
        · Ethernet in devices with Etherbone included.

        Args:
            bus (str) : Scan in all interfaces, or only for a specific interface.
            Options available:
                · "all" : Scan all interfaces.
                · "pci" : Scan only devices conneted to the PCI bus.
                · "eth" : Scan only devices conneted to Ethernet with Etherbone.
                · "serial" : Scan only devices conneted to a serial port.
            subnet(str) : Subnet IP address to scan for devices. Only used with
            option "eth" or "all". Example: subnet="192.168.7.0/24".
            numport (str) : Number of ports to scan in serial interface


        Returns:
            A dict where the keys are the seen before. The value is a list with
            ports/ip dirs. availables. When there're no conneted devices, an
            empty list is returned. A example:
            {'pci':[], 'eth':["192.168.1.3"], 'serial':["/dev/ttyUSB0",
            "dev/ttyUSB1"]}

        Raises:
            BadData : When the parameter bus is not a correct value.
        '''

        devices = {'eth':[], 'pci':[], 'serial':[]}

        # Call the child-classes' scan method
        #try :
        if sys.platform == 'linux2' : #si es linux escaneamos todos los accesos
            if bus == "pci" :
                #devices['pci'] = VUART_bridge.scan("pci")
                devices['pci'] = ConsoleBridge.scanPci()

            elif bus == "eth" :
                #devices['eth'] = VUART_bridge.scan("eth")
                devices['eth'] = ConsoleBridge.scanEth(subnet)

            elif bus == "serial" :
                #devices['serial'] = serial_bridge.scan()
                devices['serial'] = ConsoleBridge.scanSerial(numport)

            else : #if bus == "all" :

                #devices['pci'] = ConsoleBridge.scanPci()
                devices['serial'] = ConsoleBridge.scanSerial(numport)
                devices['eth'] = ConsoleBridge.scanEth(subnet)
        else: #si es windows solo serial
            devices['serial'] = ConsoleBridge.scanSerial(numport)


        #except:
            # Throw it to a upper layer
            #raise BadData(38, 'Function not found')

        return devices


    @staticmethod
    def scanPci():
        '''
        Method to scan WR devices connected to the PC.

        This method look for devices connected through the following interfaces:
        · PCIe bus.

        Args:
            subnet(str) : Subnet IP address to scan for devices. Only used with
            option "eth" or "all". Example: subnet="192.168.7.0/24".

        Returns:
            A dict where the keys are the seen before. The value is a list with
            ports/ip dirs. availables. When there're no conneted devices, an
            empty list is returned. A example:
            {'pci':[]}

        Raises:
            Error : When one of the specified interfaces could not be scanned.
        '''

        devices = []

        # Current search filters by SPEC boards : device 018d
        cmd = ["""lspci | grep %02x | cut -d' ' -f 1""" % ConsoleBridge.PCI_DEVICE_ID_SPEC]
        raw_devices = check_output(cmd, shell=True).splitlines()
        # Check vendor id -> CERN: 0x10dc
        for dev in raw_devices :
            cmd = ["cat", "/sys/bus/pci/devices/0000:%s/vendor" % dev]
            ret = check_output(cmd)[:-1]
            if int(ret,16) == ConsoleBridge.VENDOR_ID_CERN :
                devices.append(dev)

        return devices



    @staticmethod
    def scanEth(subnet="192.168.7.0/24"):
        '''
        Method to scan WR devices connected to the PC.

        This method look for devices connected through the following interfaces:
        · Ethernet in devices with Etherbone included.

        Args:
            subnet(str) : Subnet IP address to scan for devices. Only used with
            option "eth" or "all". Example: subnet="192.168.7.0/24".

        Returns:
            A dict where the keys are the seen before. The value is a list with
            ports/ip dirs. availables. When there're no conneted devices, an
            empty list is returned. A example:
            {'eth':["192.168.1.3"]}

        Raises:
            Error : When one of the specified interfaces could not be scanned.
        '''

        devices = []

        try :
            devices = EthBone.scan(subnet)
        #except BadData as e:
            #print "Fallo en es escaneo etherbone"
            #raise e
        except :
            print "Etherbone scan error"

        return devices




    @staticmethod
    def scanSerial(nports="50"):
        '''
        Method to scan WR devices connected to the PC through serial interface.

        Args:
            nports(str) : Number of port to scan

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
                _serial.flushInput()
                _serial.flushOutput()
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
