#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
This file contains the x1052 class which is a child of the abstract class GenDrv (gendrvr.py)

@file
@date Created on Apr 24, 2014
@author Benoit Rat (benoit<AT>sevensols.com)
@copyright LGPL v2.1
@see http://www.ohwr.org
@see http://www.sevensols.com
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

#-------------------------------------------------------------------------------
#                                       Import                                --
#----------------------------------------- -------------------------------------
# Import system modules
import subprocess
import os
# Import common modules
from core.gendrvr import *

class X1052(GenDrvr):
    '''
    The X1052 class has been created to interface WB access using the x1052 pcie driver.

    Currently, the read/write block data functions are not implemented
    but they might be implemented in the next future.
    '''
    info_flag='a'

    def __init__(self,LUN, show_dbg=False):
        '''
        Constructor

        Args:
            LUN : the logical unit, with this driver it is not need as we should have only one WB bus on the FPGA connected to the ARM CPU
            show_dbg : show debug info
        '''
        self.show_dbg=show_dbg
        self.load_lib("libx1052_api.so")

        self.errno=self.lib.X1052_LibInit()
        if self.errno!=0:
            raise NameError("Could not init X1052 (#%d)" %(self.errno))

        if self.show_dbg: print self.info()+"\n"
        self.open(LUN)

    def open(self, LUN):
        '''
        Open the device with the PCIe driver
        '''
        if self.hdev != -1:
            raise NameError("hDev already opened")

        self.hdev = self.lib.X1052_DeviceOpen(LUN)
        if self.hdev==0:
            raise NameError("Could not open device")

    def close(self):
        '''
        Close the device and reset hDev pointer
        '''
        if self.lib.X1052_DeviceClose():
            self.hdev = -1

    def devread(self, bar, offset, width):
        '''
        Method that do a read from the device

        Args:
            bar : BAR used by PCIe bus
            offset : offset address within bar
            width : width data size (1, 2, or 4 bytes)
        '''
        address = offset
        INTP = POINTER(c_uint)
        data = c_uint(0xBADC0FFE)
        pData = cast(addressof(data), INTP)
        ret=self.lib.X1052_Wishbone_CSR(self.hdev,c_uint(address),pData,0)
        if self.show_dbg: print "R@x%08X > 0x%08x" %(address, pData[0])
        if ret !=0:
            raise NameError('Bad Wishbone Read')
        return pData[0]


    def devwrite(self, bar, offset, width, datum):
        '''
        Method that do a write to the device

        Args:
            bar : BAR used by PCIe bus
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
            datum : data value that need to be written
        '''
        address = offset
        INTP = POINTER(c_uint)
        data = c_uint(datum)
        pData = cast(addressof(data), INTP)
        if self.show_dbg: print "W@x%08X < 0x%08x" %( address, pData[0])
        ret=self.lib.X1052_Wishbone_CSR(self.hdev,c_uint(address),pData,1)
        if ret !=0:
            raise NameError('Bad Wishbone Write @0x%08x > 0x%08x (ret=%d)' %(address,datum, ret))
        return pData[0]

    def info(self):
        """get a string describing the interface the driver is bound to """

        inf = (c_char*250)()
        self.lib.X1052_GetInfo(inf,c_char(self.info_flag))
        if self.info_flag=='a':
            return "X1052 library (%s): %s" % (self.libname,inf.value)
        else:
            return inf.value
