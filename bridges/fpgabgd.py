#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
This file contains the FPGABGD class which is a child of the abstract class GenDrv (gendrvr.py)

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
#                                   Import                                    --
#-------------------------------------------------------------------------------
# Import system modules
import subprocess
import os
# Import common modules
from core.gendrvr import *

class FPGABGD(GenDrvr):
    '''The FPGABGD class has been created to interface WB access within the WRS.

    We have create a simple library that open the device and can perform
    read/write on the WB bus.
    The read/write block data function are not implemented for this driver
    to keep it as simple as possible.
    '''

    def __init__(self,baseaddr, show_dbg=False):
        '''Constructor

        Args:
            LUN : the logical unit, with this driver it is not need as we should have only one WB bus on the FPGA connected to the ARM CPU
            show_dbg : enables debug info
        '''
        self.show_dbg=show_dbg
        self.load_lib("libfpgabgd.so")
        self.baseaddr=baseaddr
        self.sizeaddr=0 #0 is used for default size addr

        if self.show_dbg: print self.info()+"\n"
        self.open(0)

    def open(self, LUN):
        '''Open the device and map to the FPGA bus
        '''
        self.hdev=self.lib.FPGABGD_open(c_uint(self.baseaddr),c_uint(self.sizeaddr))
        if self.hdev==0:
            raise NameError("Could not open device")

    def close(self):
        '''Close the device and unmap
        '''
        self.lib.FPGABGD_close()

    def devread(self, bar, offset, width):
        '''Method that do a read on the devices using /dev/mem device

        Args:
            bar : BAR used by PCIe bus
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
        '''
        address = offset
        INTP = POINTER(c_uint)
        data = c_uint(0xBADC0FFE)
        pData = cast(addressof(data), INTP)
        ret=self.lib.FPGABGD_wishbone_RW(self.hdev,c_uint(address),pData,0)
        if self.show_dbg: print "R@x%08X > 0x%08x" %(address, pData[0])
        if ret !=0:
            raise NameError('Bad Wishbone Read')
        return pData[0]


    def devwrite(self, bar, offset, width, datum):
        ''' Method that do a write on the devices using /dev/mem device

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
        ret=self.lib.FPGABGD_wishbone_RW(self.hdev,c_uint(address),pData,1)
        if ret !=0:
            raise NameError('Bad Wishbone Write @0x%08x > 0x%08x (ret=%d)' %(address,datum, ret))
        return pData[0]

    def info(self):
        """get a string describing the interface the driver is bound to """
        inf = (c_char*60)()
        self.lib.FPGABGD_version(inf)
        return "FPGABGD library (%s): git rev %s" % (self.libname,inf.value)
