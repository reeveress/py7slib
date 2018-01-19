#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
The class in this files are designed to ease the process to Read/Write to the elements linked to the wishbone bus.
@file
@date Created on Jun 16, 2014
@author Benoit Rat (benoit<AT>sevensols.com)
@copyright LGPL v2.1
@see http://www.sevensols.com
@ingroup core
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

#--------------------------------------------------------------------------------
#                                  Import                                      --
#------------------------------------------ -------------------------------------
# Import system modules

# Import custom modules
from core.p7sException import *


class WBOperator(object):
    """
    Generic class to R/W from/to registers using the GenDrvr bus.

    This class has been designed as an helper for other classes
    in order to ease the R/W process to specific bit/field in a register.
    """

    def __init__(self, bus):
        """
        Constructor

        Args:
            bus: An instantiation of the GenDrvr bus (i.e: GennumDrvr)
        """
        self.bus=bus
        self.base_addr=0x0

    def read(self, offset):
        """
        Read a value from an offset
        """
        return self.bus.read(self.base_addr+offset)

    def write(self, offset, value):
        """
        Write a value to an offset
        """
        self.bus.write(self.base_addr+offset, value)


    def wr_bit(self, addr, bit, value):
        """
        Write a bit to a register

        Args:
            addr: Address of the register
            bit: bit position to read/write
            value:  The bit value (0/1)
        """
        reg = self.read(addr)
        if(0==value):
            reg &= ~(1<<bit)
        else:
            reg |= (1<<bit)
        self.write(addr, reg)

    def rd_bit(self, addr, bit):
        """
        Read a bit from a register

        Args:
            addr: Address of the register
            bit: bit position to read/write

        Returns:
            The bit value (0/1)
        """
        if(self.read(addr) & (1<<bit)):
            return 1
        else:
            return 0

    def rd_rfld(self,offset,position, width=1):
        """
        Read a register field

        Args:
            offset: Offset of the register
            position: Position of the field
            width: Width of the field

        Returns:
            The field value
        """
        data=self.read(offset)
        return (data >> position) & (pow(2,width)-1)

    def wr_rfld(self,offset,val, position, width=1):
        """
        Write a register field

        Args:
            offset: Offset of the register
            val:  The field value
            position: Position of the field
            width: Width of the field
        """
        data=self.read(offset)
        mask=pow(2,width)-1 << position
        data= (data & ~mask) | ((val << position) & mask)
        #print '@0x%03x < val=0x%08x (val=%d, pos=%d, mask=%08X, width=%d)' % (offset, data, val, position,mask, width)
        self.write(offset,data)



class WBPeriph(WBOperator):
    """
    Class that represent a WBPeriph with various registers and fields

    This class is a child of WBOperator in order to access easily to/from the registers
    """

    def __init__(self, bus, base_addr,name):
        self.bus = bus
        self.base_addr = base_addr
        self.name = name
        self.fields={}
        self.regs=[];

    def append(self,wbfield):
        """
        Append a WBField to the WBperiph
        """

        if self.fields.has_key(wbfield.name):
            raise NameError('Field name already used by this peripheral')
        #print wbfield
        i_reg=int(wbfield.offset/4)
        try:
            reg=self.regs.pop(i_reg)
        except IndexError:
            reg=[]
        reg.append(wbfield)
        self.regs.insert(i_reg, reg)
        self.fields[wbfield.name]=wbfield
        return wbfield


    def wr_field(self,fldname,value):
        """
        Write to a field using its name
        """

        if self.fields.has_key(fldname):
            return self.fields[fldname].write(value)
        else:
            raise PtsInvalid("field '%s' is does not exist" % (fldname))

    def rd_field(self,fldname):
        """
        Read to a field using its name
        """
        if self.fields.has_key(fldname):
            return self.fields[fldname].read()
        else:
            raise PtsInvalid("field '%s' is does not exist" % (fldname))



    def get_str(self,fldname=None):
        """
        Return a string to describe this WBField

        @param fldname: If none we will print all the fields in the periph
        otherwise we print only a specific field.
        """
        retstr=""
        if fldname==None:
            retstr+="@0x%08x : %s" %(self.base_addr,self.name)
            for reg in self.regs:
                data=self.read(reg[0].offset)
                retstr+='@0x%08X: 0x%08x' % (reg[0].offset, data)
            for fld in reg:
                retstr+=fld
        else:
            retstr+=self.fields(fldname)
        return retstr



class WBField:
    """
    Class that represent a WBField (value inside a register).
    """


    def __init__(self,prh, offset, name, pos, width=1, desc=""):
        """
        Constructor method

        Args:
            prh: The WBPeriph object
            offset: Register offset inside the WBPeriph
            name: The name of the field (used as key for WBPeriph array)
            pos: Position of the field
            width: Width of the field (1 if the field is a bit)
            desc: Message to describe a little bit more about this field (used for debug/log)
        """

        self.prh= prh
        self.name = name

        self.offset= offset-(offset%4)
        self.pos=pos+8*(offset%4)

        self.width=width
        self.desc=desc

    def __str__(self):
        if self.width==1:
            str_pos="%02d" %(self.pos)
        else:
            str_pos="[%02d-%02d]" %(self.pos+self.width-1,self.pos)
        return "%-15s => %d (@0x%08X , %s)" % (self.name, self.read(), self.prh.base_addr+self.offset, str_pos)

    def read(self):
        return self.prh.rd_rfld(self.offset,self.pos,self.width)

    def write(self,val):
        return self.prh.wr_rfld(self.offset,val,self.pos,self.width)

    def check(self, expect_val):
        """
        Check that the field as the expected value

        Returns:
            A tupple with (true/false, error message)
        """
        msg=""
        val = self.read()
        ret=(val != expect_val)
        if ret:
            msg+=val+" don't have correct value (%d)\n" %(expect_val)
        return (ret,msg)
