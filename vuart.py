#!   /usr/bin/env   python
#    coding: utf8
'''
Tool for opening an interactive shell through virtual UART.

@file
@author Felipe Torres González<ftorres@sevensols.com>
@date November 17, 2015
@copyright LGPL v2.1
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

# Imports
import argparse as arg
import sys
import socket

from core.vuart import VUART_shell


def main():
    '''
    Tool for opening an interactive shell through virtual UART.
    '''

    parser = arg.ArgumentParser(description='VUART shell for WR-LEN')

    parser.add_argument('IP', type=str, help='IP of the device')
    parser.add_argument('--input','-i',help='Execute an input script of WRPC commands')
    parser.add_argument('--output','-o',help='Save the output of an input script to a file')

    args = parser.parse_args()

    try:
        socket.inet_aton(args.IP)
    except socket.error as ip_error:
        print("Illegal IP address passed (%s)\n" % args.IP)
        exit(1)

    try:
        shell = VUART_shell(args.IP)
        if args.input:
            fin = open(args.input, 'r')
            fout = open(args.output,'a+') if args.output else None
            shell.run_script(fin, fout)
        else:
            shell.run()
    #TODO: use exceptions from vuart (not defined yet)
    except Exception as e:
        print e
        sys.stdout.write ("\033[1;31mError\033[0m: Failed connection with the WR-LEN (%s)\n" % (args.IP))
        print ("See the manual for more deatils")
    except Error as e:
        print e


if __name__ == '__main__':
    main()
