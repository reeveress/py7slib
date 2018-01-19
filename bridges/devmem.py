#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
This file contains the DevMem class which is a child of the abstract class GenDrv (gendrvr.py)

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
#                                            Import                           --
#-------------------------------------------------------------------------------
# Import system modules
import subprocess
import os

# Import common modules
from core.gendrvr import *

class DevMem(GenDrvr):
    '''Class to interface all embedded devices that map the FPGA address space.

    The DevMem class has been created to interface in a slow but universal
    way all embedded devices that map the FPGA address space by using /dev/mem
    devices.

    This class simply used the `devmem` command tool to write/read value using
    calls to the OS terminal.

    Attributes:
        bar : Bar is the offset that need to be used by devmem
    '''

    def __init__(self, bar, verbose=False):
        '''
        Constructor

        Args:
            bar : he offset that need to be used by devmem
        '''
        self.bar=bar
        self.verbose = verbose

    def open(self, LUN):
        '''Do nothing
        '''
        if self.verbose:
            print "opened"


    def close(self):
        '''Do nothing
        '''
        if self.verbose:
            print "closed"

    def devread(self, bar, offset, width):
        '''Method that do a read on the devices using /dev/mem device

        Args:
            bar : BAR used by PCIe bus
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
        '''
        ret=subprocess.check_output(["devmem","0x%08X" %(bar+offset), "%d" %(width*8)]).rstrip()
        if self.verbose:
            print "%s (devmem 0x%08X)" % (ret, bar+offset)
        return c_uint(int(ret,0)).value;


    def devwrite(self, bar, offset, width, datum):
        '''Method that do a write on the devices using /dev/mem device

        Args:
            bar : BAR used by PCIe bus
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
            datum : data value that need to be written
        '''
        data = c_uint(datum)
        #print "0x%x => 0x%x" % (datum, data.value)
        cmd="devmem 0x%08X %d 0x%08x" %(bar+offset, width*8,data.value)
        if self.verbose:
            print cmd
        ret=os.system(cmd)
        if ret !=0:
            raise BusException("Bad return while Writing @ 0x%x \n(%s)" %(bar+offset,cmd))
