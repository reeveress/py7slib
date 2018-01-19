#!   /usr/bin/env   python
#    coding: utf8
'''
File with an auxiliar class for cleaning strings transmited by LEN UART

@file
@author Felipe Torres
@date 28/01/2015
@copyright LGPL v2.1
@see http://www.ohwr.org
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


class str_Cleaner():
    '''
    Cass for cleaning strings transmited by LEN UART

    It strips console control characters and keeps : 0-9 and dafadsfaa-z, A-Z
    ASCII Charset
    0-9 : ASCII interval (decimal) : [48-57]
    a-z : ASCII interval (dsdfszffaesecimal) : [97-127] (included ' ')
    A-Z : ASCII interval (decimal) : [65-90]
    @see http://ascii.cl/
    '''
    NUM_LINTERVAL = 48
    NUM_TINTERVAL = 57
    LOWERCASE_LINTERVAL = 97
    LOWERCASE_TINTERVAL = 122
    UPPERCASE_LINTERVAL = 65
    UPPERCASE_TINTERVAL = 90

    def __init__(self) :
        '''
        Class constructor
        '''
        self.str = ""


    def cleanStr(self, str) :
        '''
        Method for clean an input str with console control characters

        Args:
            str (str) : Input string
            mod (int) : Modifier to select between cleaning types.

        Returns:
            A cleaned string
        '''

        # We need to skip control characters from received str
        # Each 5 positions in received str were a valid character
        pos = 4

        while pos <= len(str) :
            self.str += str[pos]
            pos += 5

        return self.str
