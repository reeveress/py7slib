#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
Tool to update the Software in the LM32 soft-processor etherbone/serial communication

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
import argparse as arg

from bridges.ethbone import *
#from pts_core.bridges.wb_uart import *
from periph.ipc_spiflash import *
from bridges.sdb import SDBNode


def main():
    '''
    Script for loading the LM32's Software in the WR-LEN
    '''

    parser = arg.ArgumentParser(description='WR-LEN Software Loader v1.0')

    parser.add_argument('--bus','-b',help='communication bus', choices=['EB','UART'],\
    required=True)
    parser.add_argument('--lun','-l',help='Logical unit Number (SerialPort / IP)',\
    type=str, required=True)
    parser.add_argument('--file','-f',help="RAM file",required=True)
    parser.add_argument('--debug','-d',help="Enable debug output",action='store_true')

    args = parser.parse_args()
    ## Opening Bus connection
    try:
        if args.bus.lower() == "eb":
            bus = EthBone("udp/"+args.lun,args.debug)
        #else: ##options.bus_type == "UART"
           # bus = wb_UART()
            #bus.open(options.lun)
    except BusException, e:
        print "Fatal: %s" % (e)


    flash=SpiFlash(bus, None, args.debug)
    flash.eb_sw_loader(args.file)


if __name__ == '__main__':
    main()
