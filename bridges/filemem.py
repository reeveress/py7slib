#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
This file contains the debug class FileMem which is a child of the abstract class GenDrv (gendrvr.py)

@file
@date Created on Mar 19, 2014
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
#                                  Import                                     --
#----------------------------------------- -------------------------------------
# Import system modules
from ctypes import *
import os, errno, re, sys, struct
import os.path
# Import common modules
from core.gendrvr import *


# python 2.4 kludge
if not 'SEEK_SET' in dir(os):
    os.SEEK_SET = 0

class FileMem(GenDrvr):
    '''
    This class is used for debugging or developing purpose only.

    It can fake behaviour without the need of a real device.
    '''

    fid=None

    def __init__(self, fpath):
        """Constructor method: call open()"""
        self.open(fpath)

    def __del__(self):
        self.fid.close()

    def open(self,fpath):
        """Open a read/write file using filepath"""
        self.fid = open(fpath,'r+')

    def close(self):
        """Flush and close the file"""
        self.fid.flush()
        self.fid.close()



    def find(self,address):
        """Find a value at a specific address"""
        line=self.fid.readline()
        val=0
        pos=line.find('@0x%08X:' % (address))
        if pos<0:
            self.fid.seek(0)
            lines = self.fid.read()
            pos = lines.find('@0x%08X:' % (address))
            if pos >=0:
                self.fid.seek(pos)
                line=self.fid.readline()
        if pos>=0:
            val=re.search('@0x%08X: 0x([0-9a-f]{8})' % (address),line, re.IGNORECASE).group(1)
            val=int(val,16)
        return {'pos':pos, 'val':val}


    def devread(self, bar, offset, width):
        '''
        Method that do a read on the opened file

        Args:
            bar : BAR used by PCIe bus (not need here)
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
        '''
        address = offset
        ret=self.find(address)
        print "R: @0x%08X: 0x%08x (%d)" % (address, ret['val'],ret['pos'])
        return ret['val']


    def devwrite(self, bar, offset, width,datum):
        '''
        Method that do a write of datatum on the opened file

        Args:
            bar : BAR used by PCIe bus (not need here)
            offset : address within bar
            width : data size (1, 2, or 4 bytes)
            datum : data value that need to be written
        '''
        address = offset
        wstr="@0x%08X: 0x%08x" % (address,datum)
        ret=self.find(address)
        if ret["pos"]>=0:
            self.fid.seek(ret["pos"])
        print "W: %s" % (wstr)
        self.fid.write(wstr+"\n")
