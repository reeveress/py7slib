#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
Tool to update the gateware in the SPIflash using etherbone/serial communication

For example if you want to flash a new GW for the LEN with IP 192.168.7.50 you will
need to write something like:

    ./spiflash_update --bus=EB --lun=udp/192.168.7.54 --mode=update --file=wr-len-v2.x.mcs


@file
@date Created on Jun 16, 2015
@author Benoit Rat (benoit<AT>sevensols.com)
@author Husein Gomiz (hgomiz<AT>sevensols.com)
@copyright LGPL v2.1
@see http://www.ohwr.org
@see http://www.sevensols.com
'''

import sys
import traceback
import os
import re
import subprocess
from optparse import OptionParser

from bridges.ethbone import EthBone
from periph.ipc_spiflash import *
from bridges.sdb import SDBNode
from core.gendrvr import BusException


def main():
    # Vendor ID for CERN
    VENDOR_ID_CERN = 0xce42
    # Vendor ID for SevenSolutions
    VENDOR_ID_7SOLS = 0x7501
    # WR-Mini-NIC
    WR_MININIC_RAM = 0x66cfeb52
    # WR-SPI-Flash-Update Core
    WR_SPI_FLASH = 0xae5f

    use = "Usage: %prog [--bus=uart --lun=0 --debug -file=mcsfile] "
    parser = OptionParser(usage=use, version="spiflash update v1.0")

    parser.add_option("-l", "--lun", help="Logical unit Number (SerialPort / IP)", dest="lun")
    parser.add_option("-b", "--bus", help="Bus UART/EB", dest="bus_type", default="EB")
    parser.add_option("-d", "--debug", help="Debug Flag", dest="debug", default=False, action="store_true")
    parser.add_option("-s", "--silent", help="Silent Flag", dest="silent", default=False, action="store_true")
    parser.add_option("-m", "--mode", help="cido: Check ID Only," "vo: Verify Only," "update: update flash image", dest="mode", default="cido")
    parser.add_option("-f", "--file", help="MCS file", dest="file")

    options, args = parser.parse_args()

    ## Opening Bus connection
    try:
        if options.bus_type.lower() == "eb":
            bus = EthBone("udp/%s" % options.lun, (options.mode=="test"))
            bus.silent=options.silent
        #else: ##options.bus_type == "UART"
           # bus = wb_UART()
            #bus.open(options.lun)
    except BusException as e:
        print "Fatal: %s" % (e)
        return 1

    sdb = SDBNode(bus, None)
    sdb.base = sdb.scan()
    sdb.parse()
    blockrams = sdb.findProduct(VENDOR_ID_CERN, WR_MININIC_RAM)
    spi_base = sdb.findProduct(VENDOR_ID_7SOLS, WR_SPI_FLASH)[0][1]

    # Look for the Block RAM of the MINIC 1
    ram_base = 0
    for ram in blockrams:
        if ram[1] > ram_base: ram_base = ram[1]

    if options.mode=="test":
        ##Check Endpoint Register
        bus.test_rw()

        ##Check block read/write using MiniNIC RAM.
        bus.test_rwblock(ram_base)
        return 0

    # This address must be changed if the layout changes.
    flash=SpiFlash(bus,spi_base,options.debug)

    flash.flash_update(options.mode,options.file)



if __name__ == '__main__':
    main()
