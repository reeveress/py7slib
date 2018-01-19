#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
Create all the structures to parse the Self-Describe-Bus format

This file is based on the official version 1.1 of sdb.h

@file
@date Created on Jul 20, 2015
@author Benoit Rat (benoit<AT>sevensols.com)
@copyright LGPL v2.1
@see http://www.ohwr.org/projects/fpga-config-space/wiki
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

#---------------------------------------------------------- --------------------
#                                   Import                                    --
#-------------------------------------------------------------------------------

# Import system modules
import os
from ctypes import *
import ctypes

# User defined modules
from core.gendrvr import BusWarning, BusCritical, BusException

# Define specific for SDB Flags
SDB_MAGIC                   = 0x5344422d
SDB_WB_WIDTH_MASK           = 0x0f
SDB_WB_ACCESS8              = 0x01
SDB_WB_ACCESS16             = 0x02
SDB_WB_ACCESS32             = 0x04
SDB_WB_ACCESS64             = 0x08
SDB_WB_LITTLE_ENDIAN        = 0x80
SDB_DATA_READ               = 0x04
SDB_DATA_WRITE              = 0x02
SDB_DATA_EXEC               = 0x01



class StructStr(BigEndianStructure):
    """
    Extended the structure class with an improved __str__() method

    This class is useful to parse/print all the structures from sdb.h
    """

    def __str__(self):
        msg=""
        for field_name, field_type in self._fields_:
            var=getattr(self, field_name)
            if field_type.__bases__[0] is StructStr:
#                msg+="  * %s ....\n" %(field_type.__bases__)
                msg+="%s" %(var)
            elif field_name=="vendor_id":
                 msg+="%-15s: 0x%016x" % (field_name,var)
                 if var==0x651: msg+=" (GSI)\n"
                 elif var==0x7501: msg+=" (7S)\n"
                 elif var==0xCE42: msg+=" (CERN)\n"
                 else: msg+="\n"
            else:
                msg+="%-15s: " % (field_name)
                #msg+="%-15s: %s %s" % (field_name,field_type,type(var))
                if type(var)==long or type(var)==int:
                    try:
                        fmt="0x%%0%dx\n" %(ctypes.sizeof(field_type)*2)
                    except Exception, e:
                        print e
                        fmt="0x%x\n"
                    msg+=fmt %(var)
                else:
                    msg+="%s\n" %(var)

        return msg

class sdb_product(StructStr):
    """
    product information: 44 bytes (11W)
    """
    _fields_ = [
        ("vendor_id",  c_uint64),
        ("device_id", c_uint32),
        ("version",  c_uint32),
        ("date", c_uint32),
        ("name", (c_char * 19)),
        ("record_type", c_uint8),
    ]

class sdb_component(StructStr):
    """
    component information: address + product information
    """
    _fields_ = [
        ("addr_first",  c_uint64),
        ("addr_end", c_uint64),
        ("product",  sdb_product),
    ]


class sdb_empty(StructStr):
    """
    empty component information: 64 bytes (16W)
    """
    _fields_ = [
        ("reserved",  c_int8 * 63),
        ("record_type", c_uint8),
    ]

class sdb_interconnect(StructStr):
    """
    sdb_interconnect
    This header prefixes every SDB table.
    It's component describes the interconnect root complex/bus/crossbar.
    """
    _fields_ = [
        ("sdb_magic",  c_uint32),  ##0x5344422D
        ("sdb_records", c_uint16), ##Length of the SDB table (including header)
        ("sdb_version", c_uint8),
        ("sdb_bus_type", c_uint8),
        ("sdb_component", sdb_component),
    ]



class sdb_integration(StructStr):
    """
    This meta-data record describes the aggregate product of the bus.
    For example, consider a manufacturer which takes components from
    various vendors and combines them with a standard bus interconnect.
    The integration component describes aggregate product.
    """
    _fields_ = [
        ("reserved",  c_int8 * 24),  ##0x5344422D
        ("sdb_product", sdb_product),
    ]

class sdb_device(StructStr):
    """
    This component record describes a device on the bus.

    abi_class describes the published standard register interface, if any.
    """
    _fields_ = [
        ("abi_class",  c_uint16),  # 0 = custom device
        ("abi_ver_major", c_uint8),
        ("abi_ver_minor", c_uint8),
        ("bus_specific", c_uint32),
        ("sdb_component", sdb_component),
    ]


class sdb_bridge(StructStr):
    """
    This component describes a bridge which embeds a nested bus.

    This does NOT include bus controllers, which are *devices* that
    indirectly control a nested bus.
    """
    _fields_ = [
        ("sdb_child",  c_uint64),  #Nested SDB table
        ("sdb_component", sdb_component),
    ]

class sdb_repo_url(StructStr):
    """
     Top module repository url

    An informative field that software can ignore.
    """
    _fields_ = [
        ("repo_url",  c_char * 63),
        ("record_type", c_uint8),
    ]

class sdb_synthesis(StructStr):
    """
     Top module repository url

    An informative field that software can ignore.
    """
    _fields_ = [
        ("syn_name",  c_char * 16),
        ("commit_id", c_char * 16),
        ("tool_name", c_char * 8),
        ("tool_version", c_uint32),
        ("date", c_uint32),
        ("user_name", c_char * 15),
        ("record_type", c_uint8),
    ]


class sdb_record(Union):
    """
    Generic sdb record with all possible SDB structure.
    """
    _fields_ = [
        ("empty",       sdb_empty),
        ("device",      sdb_device),
        ("bridge",      sdb_bridge),
        ("integration", sdb_integration),
        ("interconnect",sdb_interconnect),
        ("repo_url", sdb_repo_url),
        ("synthesis",sdb_synthesis),
    ]

    TYPE_INTERCONNECT = 0x00
    TYPE_DEVICE       = 0x01
    TYPE_BRIDGE       = 0x02
    TYPE_INTEGRATION  = 0x80
    TYPE_REPO_URL     = 0x81
    TYPE_SYNTHESIS    = 0x82
    TYPE_EMPTY        = 0xFF

    FLAG_BUS_WISHBONE = 0x00
    FLAG_BUS_DATA     = 0x01

    def is_type(self,type):
        return self.empty.record_type==type

    def is_component(self):
        return (self.empty.record_type & 0xFFFFFFFC)==0


    def getTypedRecord(self):
        """ Method to return the specific record of the union according to its type """
        if self.is_type(self.TYPE_INTERCONNECT):
            return self.interconnect
        elif self.is_type(self.TYPE_DEVICE):
            return self.device
        elif self.is_type(self.TYPE_BRIDGE):
            return self.bridge
        elif self.is_type(self.TYPE_INTEGRATION):
            return self.integration
        elif self.is_type(self.TYPE_REPO_URL):
            return self.repo_url
        elif self.is_type(self.TYPE_SYNTHESIS):
            return self.synthesis
        else:
            return self.empty

    def __str__(self):
        var= self.getTypedRecord()
        if (type(var)==sdb_empty) and (self.empty.record_type!=0xFF):
            raise BaseException("Sdb unknown type %0x" %(self.empty.record_type))
        return "%s:\n%s" %(type(var),var)



class SDBNode():
    """
    Main class that represent a SDB node:

    It contains:
        * an interconnect record (WB-Crossbar)
        * several records that can be linked to a child (another SDBNode)
    """
    base = None  # address of the SDB interconnect record.
    offset=0     # offset of the nested interconnect (child crossbar)
    level=0      # return its sub-level (0 for root)
    buspath_prefix=""
    debug=False

    def __init__(self,bus,base,parent=None):
        """

        Args:
            bus: instance of the gendriver class.
            base: the base address to find the SDB Root with magic header, if it is not instantiate
            the class will automatically call a scan
            parent: point to the parent structure in case we are not root.
        """
        self.parent=parent
        if parent!=None:
            self.level=parent.level+1
            self.debug=parent.debug
        self.interconnect=sdb_interconnect()
        self.elements=[]
        self.bus=bus
        self.base=base


    def parse(self,maxlevel=-1):
        """
        Parse the SDB structure

        If the "base" member has not been set this function will call the scan() method

        Args:
            maxlevel: the maximum number of nested bus we can explore (if -1 we stop when we don't find new one)
        """
        ## Check that we have a correct base, otherwise we scan it
        if self.base==None:
            self.base=self.scan()
        else:
            if self.bus.read(self.base) != SDB_MAGIC: raise BaseException("Sdb base offset 0x%08x has not a valid sdb magic" %(self.base))

        ## Read the interconnect info (Where the SDB is stored)
        self.readrecord(self.base,self.interconnect)
        #print self.interconnect
        for i in range(1,self.interconnect.sdb_records):
            #print ">>>>>>>>>>>>>>>>>> Device %s%d" %(self.buspath_prefix,i)
            el=sdb_record()
            self.readrecord(self.base + sizeof(el)*i, el)
            #print el
            n=None ##At the moment no node is appended
            if el.is_type(sdb_record.TYPE_BRIDGE) and (maxlevel>0 or maxlevel==-1):
                bridge=el.getTypedRecord()
                n=SDBNode(self.bus,bridge.sdb_child,self)
                n.buspath_prefix=self.buspath_prefix+"%d." %(i)
                n.offset=bridge.sdb_component.addr_first
                if maxlevel>0: nextlevel=maxlevel-1
                else: nextlevel=maxlevel
                n.parse(nextlevel)
            self.elements.append((el,n))

    def scan(self,mask=0x10000000):
        """
        This function scan the FPGA memory map to find a valid sdb root

        It start to check all the address starting by mask and iterate
        on the lowest address space at each iteration.

        Below a short example of how we iterate to find the sdb root:

        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        0xF0000000
        0xE0000000
        0x...
        0x10000000
        0x0F000000
        0x0E000000 <=> SDB_MAGIC (so we return)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        """

        if mask<=0x100: raise BaseException("Could not find sdb root")

        for i in range(14,-1,-1): ##TODO: Check that reverse scanning is always better
            try:
                offset=mask+i*mask
                datar=self.bus.read(offset)
                if self.debug: print "@0x%08x > 0x%08x" %(offset,datar)
                if datar==SDB_MAGIC: return offset
            except BusWarning,e:
                if self.debug: print e
                ##TODO: when bus error are well handle we can skip out of place
        return self.scan(mask >> 4)

    def findProduct(self,vendor_id,device_id, prods=None):
        """
        Find SDB product according to vendor/device ID

        Be aware that the address inside the sdb_record are relative and depend
        on the direction of the above crossbar.

        Args:
            vendor_id: The ID to describe the vendor (7501 <=> Seven Solutions)
            device_id: The ID to describe this device (WB Slave core)

        Return:
            A list of all the device found that match the vendor/device ID
            We return a tupple with the (sdb structure,full_wb_address)
        """
        if prods is None: prods = []

        for i in range(0,len(self.elements)):
            if self.elements[i][0].is_component():
                e=self.elements[i][0].getTypedRecord()
                prod=e.sdb_component.product
                if self.debug: print "%x:%x => %x:%x" %( vendor_id, device_id, prod.vendor_id, prod.device_id)
                if long(prod.vendor_id)==vendor_id and int(prod.device_id)==device_id:
                    buspath="%s%d" %(self.buspath_prefix,i+1)
                    if self.debug: print "Found Device %s %s: %x\n%s" %(buspath,prod.name,self.offset+e.sdb_component.addr_first,e)
                    prods.append((e,self.offset+e.sdb_component.addr_first,buspath))
            if self.elements[i][1]!=None:
                self.elements[i][1].findProduct(vendor_id,device_id,prods)
        return prods

    def ls(self,verbose=False):
        """
        List all the sdb peripheral

        Args:
            verbose: in case it is True we print the full list, otherwise we print only a one-line list.
        """
        if verbose==True:
            self.ls_full()
            print ""
        else:
            print "%-14s %16s %-8s  %16s  %s" %("BusPath","VendorID","ProdID","BaseAddr (Hex)", "Description")
            self.ls_brief()

    def ls_full(self):
        nspaces=self.level*3
        fmt="%%%ds" %(nspaces)
        prefix=fmt %("")

        if self.level>0: self._print_indent("|\n+++|",nspaces-3)
        print "%s+=== Interconnect %s0 (@0x%08x)" % (prefix, self.buspath_prefix,self.base)
        print "%s|" %(prefix)
        self._print_indent(self.interconnect,nspaces, "|   ")
        for i in range(0,len(self.elements)):
            print "%s|" %(prefix)
            print "%s+--- Device %s%d" %(prefix,self.buspath_prefix,i+1)
            self._print_indent(self.elements[i][0],nspaces, "|   ")
            if self.elements[i][1]!=None:
                self.elements[i][1].ls_full()

    def ls_brief(self):
        for i in range(0,len(self.elements)):
            if self.elements[i][0].is_component():
                e=self.elements[i][0].getTypedRecord()
                buspath="%s%d" %(self.buspath_prefix,i+1)
                self.ls_oneline(e,self.offset+e.sdb_component.addr_first, buspath)
            if self.elements[i][1]!=None:
                self.elements[i][1].ls_brief()

    @staticmethod
    def ls_oneline(e,offset,buspath=""):
        prod=e.sdb_component.product
        print "%-14s %016x:%08x  %16x  %s" %(buspath,prod.vendor_id,prod.device_id,offset,prod.name)


    def readrecord(self,address,record):
        """
        Read a record from the bus

        Args:
            address: address of the 64-bytes record on the WB bus.
            record: represent any kind of 64-bytes sdb_record

        Return: The record after being read
        """
        pData=cast(addressof(record), POINTER(c_uint8))
        self._readWords(address, pData,sizeof(record))
        return record

    def _readWords(self,offset,pData,nbytes):
        """ Read words on the bus and fill it using a pointer on a buffer data """
        for i in range(0,nbytes):
            #pData[i]=BitManip.swap32(self.bus.read(offset+i*4))
            mod=i%4
            if mod==0:
                rd=self.bus.read(offset+i)
                tmp=(rd & 0xFF000000) >> 24
            elif mod==1:
                tmp=(rd & 0x00FF0000) >> 16
            elif mod==2:
                tmp=(rd & 0x0000FF00) >> 8
            else:
                tmp=(rd & 0x000000FF)
            pData[i]=tmp
            #print "%d: 0x%x" %(i,pData[i])
        return pData


    def _print_indent(self,obj,nspace,sep=""):
        """
        Private function to print multiple lines with indentation

        Args:
            obj: the obj/string to be print (must overload the __str__() function)
            nspace: the number of space to indent
            sep: The separator between space and text
        """
        s = "%s" % (obj)
        print "\n".join((nspace * " ") + sep + i for i in s.splitlines())
