#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
Tool to read/parse the sdb format from the FPGA.

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
from bridges.wb_uart import *
from bridges.sdb import *
from core.ptsexcept import *
from core.ptslogger import PTSLogger
from core.tools import KeyInput

def auto_int(x):
    """ Convert hexadecimal to int """
    return int(x,0)

def main():

    parser = arg.ArgumentParser(description='Tool to read/parse the sdb format from the FPGA')

    parser.add_argument('--debug','-d',help="Enable debug output",action='store_true')
    parser.add_argument('--verbose','-v',help="Print Sdb in full version",action='store_true')
    parser.add_argument('--address', '-a', help="SDB Bus address (Hex format)",type=auto_int,default=None)
    parser.add_argument('--bus','-b',help='communication bus', choices=['EB','UART'],required=True)
    parser.add_argument('--lun','-l',help='Logical unit Number (Bus Index / SerialPort / IP)',type=str, required=True)
    parser.add_argument('--find','-f',help='Find a specific device vendor_id:dev_id',default=None)



    args = parser.parse_args()

    ## Opening Bus connection
    try:
        if args.bus.lower() == "eb":
            bus = EthBone(args.lun,args.debug)
        elif args.bus.lower() == "uart":
            plog=PTSLogger("/tmp/info.log","/tmp/error.log",args.debug)
            bus = wb_UART(plog)
            bus.open(args.lun)
        else:
            print "Unknown bus"
            return
    except BusException, e:
        print "Fatal: %s" % (e)

    ##TODO: add sdb to detect where we should load on any bus.

    sdbroot=SDBNode(bus,args.address)
    sdbroot.debug=args.debug
    sdbroot.parse()

    if args.find==None:
        sdbroot.ls(args.verbose)
    else:
        ids=str.split(args.find,":")
        prods=sdbroot.findProduct(long(ids[0],0),int(ids[1],0))
        for p in prods:
            SDBNode.ls_oneline(p[0],p[1],p[2])


    print ""

if __name__ == '__main__':
    main()
