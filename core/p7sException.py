#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
Custom exceptions

@file
@date Created on Jul 20, 2015
@author Benoit Rat (benoit<AT>sevensols.com)
@copyright LGPL v2.1
@see http://www.ohwr.org/projects/fpga-config-space/wiki
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


import ewberrno as errno


class p7sException(Exception) :
    # definir los códigos de error
    def __init__(self, errcode, msg) :
        '''
        Constructor

        Formats output string
        '''
        self.err = errno.Ewberrno()
        self.errcode = errcode
        self.errmsg = msg
        
        
    def __str__(self):

        if self.errmsg != '':
            errstr = "Error code: " + str(self.errcode) + ": " + "%s (%s)" % (self.err.errdict[self.errcode], self.errmsg)
        else:
            errstr = "Error code: " + str(self.errcode) + ": " + "%s" % (self.err.errdict[self.errcode])
        return errstr

class Retry(p7sException) :
    '''
    This exception indicates to caller that the operation failed and it should be retried.
    '''
    #BADINTERFACE = (1,"Wrong interface selected. List of available interfaces: ")

class BadData(p7sException) :
    '''
    Exception used to indicate that any of the passed parameters are invalid.
    '''
    '''messages = {}
    messages[1] = "No valid interface selected. Valid interfaces are : "
    messages[2] = "No valid IP : "
    messages[3] = "No valid PCI port : "'''

class Error(p7sException) :
    '''
    Exception used for critical errors that should stop the execution of the caller.
    '''
    '''messages = {}
    messages[1] = "Not availabe: "
    messages[2] = "Error closing driver : "'''
