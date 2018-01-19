#!   /usr/bin/env   python
#    coding: utf8
'''
The VUART_bridge class allows to connect with WR devices over Etherbone or PCI bus.

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
import re
import time
from subprocess import check_output

# User defined imports
from consolebridge import ConsoleBridge
from ethbone import EthBone
from core.p7sException import p7sException
from bridges.sdb import SDBNode
from core.gendrvr import BusCritical, BusWarning


class VUART_bridge(ConsoleBridge):
    '''
    Class to handle connection with WR devices through the Virtual UART.

    This class implements the interface defined in ConsoleBridge abstract class
    for devices connected on the PCI bus or Ethernet (using Etherbone).
    '''
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

    def __init__(self, interface, port, verbose=False):
        '''
        Constructor

        Args:
            interface (str) : Indicates the bus used for the connection: "eth" or "pci".
            port (str) : Port number or IP/mask. Examples: "01:00.0" for pci, and
            "192.168.1.1" for ethernet.
            verbose (bool) : Enables verbose output

        Raises:
            BadData exception if any of the input parameters are not valid.
        '''
        # Input control
        if interface != "eth" and interface != "pci":
            raise BadData(1, "eth/pci")
        if interface == "eth" and not re.match(self.valid_ip,port):
            raise BadData(2, port)
        if interface == "pci" and not re.match(self.valid_pci,port):
            raise BadData(3, port)

        self.interface = interface
        self.port = "udp/"+port
        self.bus = None
        self.verbose = verbose

    def open(self, ethbone_dbg=False):
        '''
        Method to open a new connection with a WR device.

        Args:
            ethbone_dbg (bool) : Flag to enable verbose output for the EtherBone driver.

        Raises:
            ConsoleError : When the specified device fails opening.
        '''
        if self.interface == 'eth':
            try:
                self.bus = EthBone(self.port, False)
            except BusCritical:
                BadData(4, self.port)
        elif self.interface == 'pci':
            raise Error(1, "PCI bus not implemented")

        # Look for VUART address in the sdb bus
        sdb = SDBNode(self.bus, None)
        sdb.base = sdb.scan()
        sdb.parse()
        self.VUART_OFFSET = sdb.findProduct(self.VENDOR_ID_CERN, self.WR_UART_ID)[0][1] # Check this assignment
        if self.verbose:
            print("VUART address is 0x%x" % (self.VUART_OFFSET))

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
            raise algo

        if self.verbose:
            print("Erasing old content of rx buffer in the VUART")

        self.sendCommand("\x1b\r")

    def sendCommand(self, cmd):
        '''
        Method to pass a command to the Virtual UART module of a WR Device

        This method writes a command to the input and retrieves the device
        response (if any). If buffered is used, the driver will package multiple
        rw_cmd commands into a same packet.

        TODO: Implement buffered logic

        Note for developers:
        Returned value is type bytearray. To avoid conflicts between OS used
        codification, decode should be done in the caller. For example use:
        vuart.sendCommand("ip").decode("utf-8")

        Args:
            cmd (str) : Command

        Returns:
            A bytearray with the output of the command sent to the WR Device.

        Raises:

        '''
        if self.verbose and cmd != "\r":
            print("Sending command '%s'" % (cmd))
        bytes = []

        # Wait for ready bit
        timeout_cnt = 0
        ready = self.bus.read(self.VUART_OFFSET+self.VUART_TX_REG) & self.VUART_RDY_MSK
        while not ready:
            time.sleep(1)
            timeout_cnt += 1
            if timeout_cnt >= self.MAX_TIMEOUT:
                #raise Error()  # virtual uart is not ready
                return 'Error: virtual UART is not ready' # virtual uart is not ready

        bytes = bytearray(cmd)
        bytes.append(13) # insert \r
        try:
            for b in bytes:
                self.bus.devwrite(None,offset=self.VUART_OFFSET+self.VUART_TX_REG, width=4, datum=b)
                #time.sleep(0.0008)
                time.sleep(0.05)
            time.sleep(0.5)
            rx_raw = self.bus.read(self.VUART_OFFSET+self.VUART_RX_REG)
            if rx_raw & self.VUART_RDY_MSK:
                cnt = (rx_raw & self.VUART_RX_CNT_MSK) >> 9

                while cnt > 0:
                    bytes.append(rx_raw&self.VUART_RX_DAT_MKS)
                    rx_raw = self.bus.read(self.VUART_OFFSET+self.VUART_RX_REG)
                    cnt -= 1

            # The output from VUART contains the sent command twice, remove it
            if 'wrc#' in bytes:
                r_bytes = bytes.index('\n')+1
                return bytes[r_bytes:-6]  # Remove the final "\r\nwrc#"
            else :
                return bytes
        except BusWarning as e:
            raise e


    def devwrite(self, bar, offset, width, datum):
        '''
        Method to write a register through EtherBone bus

        This method enables the use of this driver like it was a gendrvr child.

        Args:
            bar : BAR used by PCIe bus
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
            datum : data value that need to be written
        '''
        #TODO: put the following setences inside a try-except block
        return self.bus.devwrite(bar, offset, width, datum)

    def devread(self, bar, offset, width):
        '''
        Method read a register through EtherBone bus

        This method enables the use of this driver like it was a gendrvr child.

        Args:
            bar : BAR used by PCIe bus (Not used)
            offset : address within bar
            width : data size (1, 2, or 4 bytes) => Must be 4 bytes
        '''
        #TODO: put the following setences inside a try-except block
        return self.bus.devread(bar, offset, width)

    @staticmethod
    def scan(bus="all", subnet="192.168.7.0/24"):
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
            subnet(str) : Subnet IP address to scan for devices. Only used with
            option "eth" or "all". Example: subnet="192.168.7.0/24".

        Returns:
            A dict where the keys are the seen before. The value is a list with
            ports/ip dirs. availables. When there're no conneted devices, an
            empty list is returned. A example:
            {'pci':[], 'eth':["192.168.1.3"]}

        Raises:
            Error : When one of the specified interfaces could not be scanned.
        '''

        devices = {'eth':[], 'pci':[]}

        if bus == 'all' :
            devices['pci'] = VUART_bridge.scan(bus='pci')['pci']
            devices['eth'] = VUART_bridge.scan(bus='eth')['eth']

        elif bus == "pci" :
            # Current search filters by SPEC boards : device 018d
            cmd = ["""lspci | grep %02x | cut -d' ' -f 1""" % VUART_bridge.PCI_DEVICE_ID_SPEC]
            raw_devices = check_output(cmd, shell=True).splitlines()
            # Check vendor id -> CERN: 0x10dc
            for dev in raw_devices :
                cmd = ["cat", "/sys/bus/pci/devices/0000:%s/vendor" % dev]
                ret = check_output(cmd)[:-1]
                if int(ret,16) == VUART_bridge.PCI_VENDOR_ID_CERN :
                    devices['pci'].append(dev)

        elif bus == "eth" :
            try :
                devices['eth'] = EthBone.scan(subnet)
            except BadData as e:
                raise e

        return devices
