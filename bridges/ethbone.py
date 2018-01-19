#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
This file contains the etherbone class which is a child of the abstract class GenDrv (gendrvr.py)


Parse etherbone packet with wireshark
=====================================

Copy s4n.lua protocol.
-----------------------

Then if you want to read the lua protocol you need to copy the file `spec/etherbone.lua` from etherbone repo to the wireshark directory

    * Under windows: `C:\\Program Files\\Wireshark`
    * Under ubuntu: `/usr/share/wireshark/`


Activate LUA script.
----------------------

Go to the wireshark directory and edit the file: `init.lua`
You need to replace the two following lines at the beginning of the file:

    run_user_scripts_when_superuser = false
    if running_superuser then

By:

    run_user_scripts_when_superuser = true
    if running_superuser_back then


And add to the end of the file the line

    dofile(DATA_DIR.."etherbone.lua")

Install lua libraries
----------------------

    sudo apt-get install lua5.1 lua-bitop


@file
@date Created on Jun 16, 2015
@author Benoit Rat (benoit<AT>sevensols.com)
@author Felipe Torres (ftorres<AT>sevensols.com)
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
import sys
from ctypes import *
import time
import struct
import math
import platform
import binascii
from subprocess import check_output

# Import common modules
from core.gendrvr import *
from core.p7sException import p7sException

EB_PROTOCOL_VERSION = 1
EB_ABI_VERSION      = 0x04
EB_BUS_MODEL        = [0x44,0x88][sys.maxsize > 2**32]
EB_MEMORY_MODEL     = 0x0000
EB_ABI_CODE         = ((EB_ABI_VERSION << 8) + EB_BUS_MODEL + EB_MEMORY_MODEL)

PYDIR=os.path.dirname(os.path.abspath(__file__))

def py_cb_func(user, dev, op, status):
     if status: raise NameError('Callback Error: %s' % (status))
     print "%x" %(status)

# Import Etherbone structures
class eb_handler(Structure):
     _fields_ = [("sdb_dev", POINTER(c_uint)),
                 ("eb_data", POINTER(c_uint)),
                 ("eb_stat_r", POINTER(c_uint)),
                 ("eb_stat_w", POINTER(c_uint))]



class EthBone(GenDrvr):
    '''The EthBone class has been created to interface WB access using network and etherbone core.

    To use this class you must:
        * Have etherbone core installed as master of the WB crossbar
        * Have set an IP in the lm32 of your device (You might use bootp).
        * Have installed the libetherbone.so in your system

    The read/write block data functions are implemented using transaction.
    This need to be improved.
    '''

    EB_DATAX = 0x0F
    EB_ADDRX = 0xF0

    EB_ENDIAN_MASK   = 0x30
    EB_BIG_ENDIAN    = 0x10
    EB_LITTLE_ENDIAN = 0x20

    EB_OK        = 0  # success


    def __init__(self,LUN, verbose=False):
        '''Constructor

        Args:
            LUN : the logical unit, in etherbone we use a netaddress format given by:
            show_dbg : enables debug info
        '''

        if verbose: print "LD_LIBRARY_PATH=%s" % (os.getenv('LD_LIBRARY_PATH'))

        self.load_lib("%s/../lib/libetherbone.so" % PYDIR)

        ##Create empty ptr on structure used by ethbone
        self.socket    = c_uint(0)
        self.device    = c_uint(0)
        self.operation = c_uint(0)
        self.wcrc      = 0

        ##Setup arguments
        self.LUN=LUN
        self.verbose=verbose
        if self.verbose: print self.info()+"--\n"

        ##Setup variables
        self.addr_width=self.EB_ADDRX
        self.data_width=self.EB_DATAX
        self.attempts=3
        self.silent=True
        self.format=c_uint8(self.EB_BIG_ENDIAN | self.data_width)


        ##Open the device
        if LUN!="": self.open(LUN)

    def __del__(self):
        self.close()

    def open(self, LUN):
        '''Open the device and map to the FPGA bus
        '''
        status=self.lib.eb_socket_open(EB_ABI_CODE, 0, self.addr_width|self.data_width, self.getPtrData(self.socket))
        if status: raise BusCritical('failed to open Etherbone socket: %s\n' % (self.eb_status(status)));

        if self.verbose: print "Connecting to '%s' with %d retry attempts...\n" % (LUN, self.attempts);
        status=self.lib.eb_device_open(self.socket, LUN, self.EB_ADDRX|self.EB_DATAX, self.attempts, self.getPtrData(self.device))
        if status: raise BusCritical("failed to open Etherbone device: %s\n" % (self.eb_status(status)));

    def close(self):
        '''Close the device and unmap
        '''
        if (self.device.value & 0xFFFF)==0xFFFF: return 0

        status=self.lib.eb_device_close(self.device)
        if status: raise BusCritical("Close device: %s\n" % (self.eb_status(status)));
        self.device=c_uint(0)

        status=self.lib.eb_socket_close(self.socket)
        if status: raise BusCritical("Close socket: %s\n" % (self.eb_status(status)));
        self.socket=c_uint(0)

    def enable_silent_close(self,enable=True):
        '''Enable silent close (When writing a block don't ask to readback the values)
        '''
        self.silent=enable


    def devread(self, bar, offset, width):
        '''Method that do a cycle read on the devices using ed_device_read()

        Convenience methods which create single-operation cycles and it is
        equivalent to: eb_cycle_open, eb_cycle_read, eb_cycle_close.


        Args:
            bar : BAR used by PCIe bus (Not used)
            offset : address within bar
            width : data size (1, 2, or 4 bytes) => Must be 4 bytes
        '''
        address = offset

        UINT32P = POINTER(c_uint32)
        data = c_uint32(0xBADC0FFE)
        pData = cast(addressof(data), UINT32P)

        user_data=c_uint32(0)
        cb=c_uint(0)


        status=self.lib.eb_device_read(self.device,c_uint(address),self.format,pData,user_data,cb)
        if self.verbose: print "R@x%08X > 0x%08x" %(address, pData[0])
        if status: raise BusWarning('Bad Etherbone Read: %s' % (self.eb_status(status)))
        return pData[0]


    def devwrite(self, bar, offset, width, datum):
        ''' Method that do a cycle write on the devices using ed_device_write()

        Convenience methods which create single-operation cycles and it is
        equivalent to: eb_cycle_open, eb_cycle_write, eb_cycle_close.

        Args:
            bar : BAR used by PCIe bus (Not used)
            offset : address within bar
            width : data size (1, 2, or 4 bytes) => Must be 4 bytes
            datum : data value that need to be written
        '''
        address = offset
        data = c_uint32(datum)

        user_data=c_uint32(0)
        cb=c_uint(0)

        if self.verbose: print "W@x%08X < 0x%08x" %( address, datum)
        status=self.lib.eb_device_write(self.device,c_uint(address),self.format,data,user_data,cb)
        if status: raise BusWarning('Bad Wishbone Write @0x%08x > 0x%08x : %s' % (address, datum, self.eb_status(status)))
        return data


    def devblockread(self, bar, offset, bsize, incr=0x4):
        '''Method that do a multiple cycle-read to read a data block

        WARNING: THE CALLBACK CALL OF THIS FUNCTION IS NOT WORKING AT THE MOMENT.

        Call back:
        http://stackoverflow.com/questions/7259794/how-can-i-get-methods-to-work-as-callbacks-with-python-ctypes

        Args:
            bar : BAR used by PCIe bus (Not used)
            offset : address at the device
            bsize: The size in bytes of data to read (Should be multiply by 4)
            incr: By default we increment the direction by 4 because we are reading 32bit words,
            but if we want to read from a FIFO we should use incr=0x0

        Returns:
            A list of 32bits words
        '''
        UINT32P = POINTER(c_uint32)
        cycle       = c_uint(0)

#        user_data   = c_uint32(0xDEADBEEF)
#        CBFUNC = CFUNCTYPE(None, c_uint16, c_uint16, c_uint16,c_int)
#        cb          = CBFUNC(py_cb_func)
#        pUData = cast(addressof(user_data), UINT32P)

        dataVec= (c_uint32*(bsize/4))()

        ldata=[]
        addr=offset
        i=0
        status= self.lib.eb_cycle_open(self.device,0,0,self.getPtrData(cycle))
        if status: raise BusWarning('Cycle open : 0x%x, %s' % (offset,self.eb_status(status)))
        while i<bsize:
            pData = cast(addressof(dataVec)+i, UINT32P)
            self.lib.eb_cycle_read(cycle,addr,self.format,pData)
            addr=addr+incr
            i=i+4
        status=self.lib.eb_cycle_close(cycle)
        if status: raise BusWarning('Cycle close: %s' % (self.eb_status(status)))

        ###Convert the c_uint32 array to list of c_uint32
        ldata=[]
        for d in dataVec: ldata.append(d)

        ## Print the result if we are using verbose
        if self.verbose:
            addr=offset
            for d in dataVec:
                print "@x%08X > %8x" % (addr, d)
                addr=addr+incr

        return ldata


    def devblockwrite(self, bar, offset, ldata, incr=0x4):
        '''Method that do a multiple cycle-writes to write a data block

        Args:
            bar : BAR used by PCIe bus (Not used)
            offset : address in the device
            ldata : A list of 32bits words
            incr: By default we increment the direction by 4 because we are writing 32bit words,
            but if we want to write into a FIFO we should use incr=0x0
        '''

        cycle       = c_uint(0)
        user_data   = c_uint32(0)
        cb          = 0 #NULL pointer


        addr=offset
        status= self.lib.eb_cycle_open(self.device,user_data,cb,self.getPtrData(cycle))
        if status: raise BusWarning('Cycle open : 0x%x, %s' % (offset,self.eb_status(status)))
        for data in ldata:
            ##Chequear endianess de format
            if self.verbose: print "@x%08X > %8x" % (addr, data)
            self.lib.eb_cycle_write(cycle,addr,self.format,c_uint32(data))
            self.wcrc=binascii.crc32(c_uint32(data), self.wcrc)
            addr=addr+incr
        if self.silent:
            status=self.lib.eb_cycle_close_silently(cycle) #Close without asking acknowledgment of the device (faster)
        else:
            status=self.lib.eb_cycle_close(cycle)
        if status: raise BusWarning('Cycle close: %s' % (self.eb_status(status)))


        return 0;



    def eb_status(self,status):
        ''' Print the status code returned by libetherbone'''

        if status==0: return "OK"

        statab={}
        statab[1]=("EB_FAIL","system failure")
        statab[2]=("EB_ADDRESS","invalid address")
        statab[3]=("EB_WIDTH","impossible bus width")
        statab[4]=("EB_OVERFLOW","cycle length overflow")
        statab[5]=("EB_ENDIAN","remote endian required")
        statab[6]=("EB_BUSY","resource busy ")
        statab[7]=("EB_TIMEOUT","timeout")
        statab[8]=("EB_OOM","out of memory")
        statab[9]=("EB_ABI","library incompatible with application")
        statab[10]=("EB_SEGFAULT","one or more operations failed")

        if status<0 and status>-11:
            desc=statab[-status];
            return "%d=>%s (%s) " %(status,desc[0],desc[1])

        return "%d=>Unknown" %(status)

    def info(self):
        """get a string describing the interface the driver is bound to """
        return "Etherbone library (%s v%d): %s" % (self.libname,EB_PROTOCOL_VERSION,self.LUN)


    def test_rw(self,EP_offset=0x30100):
        '''
        Method to test read/write WB cycle using endpoint

        Args:
            EP_offset=The offset of the endpoint
        Raises:
            Exception: when the there is an error.
        '''
        REG_MACL=0x28
        REG_ID=0x34

        bus=self

        ##Check the CafeBabe ID
        id=(bus.read(EP_offset | REG_ID))
        print "0x%X" % id
        if id != 0xcafebabe: raise BaseException("Error reading ID")
        else: print "OK"

        ## Toogle the lowest 16bit of MAC address.
        macaddr=EP_offset | REG_MACL
        oldmac=(bus.read(macaddr))
        newmac= (oldmac & 0xFFFF0000) | (~oldmac & 0xFFFF)
        print "old=0x%X > new=0x%X" % (oldmac,newmac)
        bus.write(macaddr,newmac)
        rbmac= bus.read(macaddr)
        print "0x%X" % rbmac
        if newmac!=rbmac:  raise BaseException("Error writing new MAC")
        else: print "OK"
        bus.write(macaddr,oldmac)
        rbmac=(bus.read(macaddr))
        if oldmac!=rbmac: raise BaseException("Error writing old MAC")
        else: print "OK"

    def test_rwblock(self,RAM_offset=0x0, nwords=128):
        '''
        Method to test multiple read/write WB cycles using RAM_offset

        Args:
            RAM_offset=The offset of the RAM so we can read write

        Raises:
            Exception: when there is an error during test.
        '''

        print "test R/W block"
        dataw=[]
        for i in range (0,nwords):
            dataw.append(i<<24 | i << 16 | i << 8 | i)

        self.devblockwrite(0, RAM_offset, dataw,4)
        d_start=self.read(RAM_offset)
        d_mid=self.read(RAM_offset+4*(nwords/2))
        d_end=self.read(RAM_offset+4*(nwords-1))
        msg=""
        pos=0
        if d_start!=dataw[pos]:
            msg=msg+"@0x%08x: writen=0x%08x, readback=0x%08x " %(RAM_offset+4*pos,dataw[pos],d_start)
        pos=nwords/2
        if d_mid!=dataw[pos]:
            msg=msg+"@0x%08x: writen=0x%08x, readback=0x%08x " %(RAM_offset+4*pos,dataw[pos],d_mid)
        pos=nwords-1
        if d_end!=dataw[pos]:
            msg=msg+"@0x%08x: writen=0x%08x, readback=0x%08x " %(RAM_offset+4*pos,dataw[pos],d_end)
        if msg!="": raise BaseException(msg)

        datar=self.devblockread(0, RAM_offset, len(dataw)*4,4)

        if datar != dataw:
            for i in range(0,len(dataw)):
                print "%3d x%08x " % (i,dataw[i])
            raise BaseException("Error reading data block")


    def dataToByteArray(self,data_list,bytearray_list=[]):
        '''
        Convert list of hexadecimal characters to byte array

        Args:
            data_list=List of string in the format
            bytearray_list=Optional byte array that can be append

        Returns:
            A list of bytearray for each lines
        '''

        for line in data_list:
            hex_line=line.decode("hex")
            hex_array=bytearray(hex_line)
            bytearray_list.append(hex_array)

        return bytearray_list




    def wordsToPackets(self,data_words,data_packets=[],packetLen=128):
        '''Pack a list of words into a list of packets

        Args:
            data_words: A list of 32bits data
            data_packets: The list where we will store each packets
            packetLen: The number of words in the packets (Must be inferior to < MAXBYTE_PKTDATA/4)

        Returns:
            The list of data packets composed of {packetLen x 32bit words}
        '''
        # the 4 bytes words are grouped in "packetLen" words packets
        for i in range(0,len(data_words),packetLen):
            if i<(len(data_words)-len(data_words)%packetLen):
                tmpPacket=[]
                for k in range(0,packetLen):
                    tmpPacket.append(data_words[i+k])
                #tmpPacket.append(0xa0b1c2d4)
                data_packets.append(tmpPacket)
            else:
                last_packet=[]
                for l in range(0,len(data_words)%packetLen):
                    last_packet.append(data_words[i+l])
                data_packets.append(last_packet)
        return data_packets


    @staticmethod
    def scan(options) :
        '''
        Method for scan the bus to find WR devices connected.

        This method is aided by "fping" to make a fast scan. If "fping" is not
        available in the system, a slow scan will be performed (bcast vs. individual
        ping). Also Etherbone support must be installed in the system.

        Args:
            options (str) : subnet IP and mask to make the scan. Example: "192.168.1.0/24"

        Returns:
            A list of ports where WR devices are connected.

        Raises:
            BadData: if "options" param doesn't contains a valid ip/mask.
        '''
        if options == None or type(options) != type("") :
            raise BadData(str(options))

        subnet = options
        devices = []

        # If fping is installed, only check with eb-discover alive IPs
        if not os.system("command -v fping > /dev/null") :   # FAST MODE
            # Retrieve a list of alive devices in the subnet
            cmd = """fping -C 1 -q -g %s 2>&1 | grep -v \": -\"""" % (subnet)
            raw_alive_devs = check_output(cmd,shell=True).splitlines()
            unknown_devices = [None, ] * len(raw_alive_devs)
            i = 0
            for dev in raw_alive_devs :
                unknown_devices[i] = dev.split(":")[0].rstrip(' ')
                i += 1
            raw_alive_devs = None

            # Now check which ones are WR devices using eb-discover
            for udev in unknown_devices :
                cmd = "%s/../bin/eb-discover" % PYDIR
                args = "udp/%s" % (udev)
                ret = check_output([cmd, args])
                if ret != '' : # is a WR device
                    devices.append(udev)

        else :                                              # SLOW MODE
            # Scan to find WR devices in the network
            ip, bcast = subnet.split("/")
            end = int( (( math.ceil((32-int(bcast)) / 8.0) % 3) * 2) % 3 )
            lip = ip.split(".")[:end+1]

            buildNextSubnet = lambda root : root.append('0')
            # Generate next ip
            nextIP = lambda ip : ip.append( str( int(ip.pop())+1 ) ) if int(ip[-1]) < 255 else False
            # Check wether a ip direction is complete
            isLastByte = lambda ip : (len(ip) == 4) if (type(ip) == type(list())) else (len(ip.split(".")) == 4)

            def checkDevices(ip,devices) :
                for i in range(1,255) :
                    ip[-1] = str(i)
                    #print "probando ip: %s" % ('.'.join(ip))
                    if isLastByte(ip) :
                        cmd = "%s/../bin/eb-discover" % PYDIR
                        args = "udp/%s" % (ip if type(ip) == type("") else '.'.join(ip))
                        ret = check_output([cmd, args])
                        if ret != '' : # is a WR device
                            devices.append('.'.join(ip))
                        if int(ip[-1]) == 254 : return

                    else :
                        checkDevices( buildNextSubnet(ip) )


            buildNextSubnet(lip)
            checkDevices(lip,devices)

        return devices
