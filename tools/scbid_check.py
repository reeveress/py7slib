#!   /usr/bin/env   python
#    coding: utf8
'''
Tool to check if multiple SCB serial numbers are used for the same WRS.

@file
@author Felipe Torres
@date August 25, 2015
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
import sys
import argparse as arg

def main() :
    '''
    Script for checking if multiple SCB serial numbers are used for the same White Rabbit Switch.

    This script reads the file writed by wrs001_version test where it is associated
    a SCB serial number to the random identifier of the WRS.

    In order learn how to use this script use the option "-h".

    Returns:
        A message that indicates if a random ID is used on multiple SCB s/n.
    '''

    parser = arg.ArgumentParser(description = 'SCB ID checker v1.0')

    parser.add_argument('--input', '-i', help = 'Input file with ID-SCB associations',
    type = str, required = True)

    args = parser.parse_args()

    try :
        ifile = open(args.input, 'r')
    except Exception as error :
        print("Error opening file '%s'" % (args.input))
        exit(1)

    id_dict = {}
    hoax = {}
    flag = False
    lines = ifile.readlines()
    for line in lines :
        rid,scbsn = line.split(" - ")
        scbsn = scbsn[:-1] # Remove trailing \n
        try :
            temp = id_dict[rid]
        except KeyError :
            id_dict[rid] = []

        id_dict[rid].append(scbsn)

    # Checking
    for key in id_dict :
        first = id_dict[key][0]
        for i in id_dict[key] :
            if i != first :
                hoax[key] = id_dict[key]
                break

    print("%d IDs analyzed" % (len(lines)))
    if hoax != {} :
        print("Multiple SCB serial numbers for the same RandomIDs founded :")
        for key,values in hoax.items():
            print("\tSerial Numbers:")
            sys.stdout.write("\t")
            already_listed = []
            for i in values :
                if i in already_listed: continue
                sys.stdout.write("%s, " % (i))
                already_listed.append(i)
            print("\n\t-> %s\n" % (key))

    else :
        print("No coincidences founded.")

if __name__ == '__main__':
    main()
