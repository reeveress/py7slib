#!   /usr/bin/env   python
#    coding: utf8
'''
Script to write the SFP calibration values to a WR Device (using WRCORE commands)

@file
@author Felipe Torres
@date Sep. 22, 2015
@copyright LGPL v2.1
@see http://www.ohwr.org
@see http://www.sevensols.com
@ingroup tools
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
# System imports
import argparse as arg
from ConfigParser import SafeConfigParser
import time
import sys

# User defined imports
from bridges.VUART_bridge import *
from bridges.serial_bridge import *

def main():
    '''
    Tool for writing the SFP Data Base and Init script of a WR Device (with WRCORE)
    '''
    sfp_db = {}
    sfp_db['wr0-blue'] = []
    sfp_db['wr1-blue'] = []
    sfp_db['wr0-violet'] = []
    sfp_db['wr1-violet'] = []

    SFP_BLUE = "sfp add AXGE-1254-0531"
    SFP_VIOLET = "sfp add AXGE-3454-0531"

    parser = arg.ArgumentParser(description='EEPROM writing tool for WRCORE')

    parser.add_argument('--bus','-b',help='Bus',choices=['ethbone','serial'], \
    required=True)
    parser.add_argument('--lun','-l',help='Logical Unit (IP/Serial Port)',type=str,required=True)
    parser.add_argument('--input','-i',help='Input .ini file', type=str, required=True)
    parser.add_argument('--debug','-d',help='Enable debug output',action="store_true", \
    default=False)
    args = parser.parse_args()

    if args.bus == 'ethbone':
        uart = VUART_bridge('eth', args.lun, args.debug)
    else:
        uart = SerialBridge(port="/dev/ttyUSB%s" % args.lun, verbose=args.debug)
    # Hack for new releases of WRC-2P
    uart.open(interchartimeout=0.01)

    parser = SafeConfigParser()
    ret = parser.read(args.input)
    if ret == []:
        print("%s could not be opened" % (args.input))

    # Write the delays for the SFP ports
    if "ports" in parser.sections():
        print("Writing the port calibration values...")
        uart.sendCommand("sfp erase")
        time.sleep(0.5)  # For serial

        # Every readen port is a combination of (SFP-SN@PORT,(tx,rx,alpha))
        for port in parser.items("ports"):
            sfpsn, p = port[0].split('@')
            sfpsn = sfpsn.upper()  # The parser reads the chars in lowercase
            dtx, drx, alpha = port[1].split(',')

            cmd = "sfp add %s %s %s %s %s" % (sfpsn, p, dtx, drx, alpha)
            uart.sendCommand(cmd)
            time.sleep(0.5)  # For serial

    # Write the init script
    if "init" in parser.sections():
        print("Writing init script...")
        uart.sendCommand("init erase")
        for item in parser.items("init"):
            time.sleep(0.5)  # For serial
            uart.sendCommand("init add %s" % item[1])

    print("Configuration writed")

if __name__ == '__main__':
    main()
