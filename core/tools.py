#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
The class and methods here still needs a little bit of clean-up
@file
@date Created on Mar 19, 2014
@author Benoit Rat (benoit<AT>sevensols.com)
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

#-------------------------------------------------------------------------------
#                                    Import                                   --
#-------------------------------------------------------------------------------
# Import system modules
import sys, select
#import tty,termios, time
from ctypes import *

# Import custom modules


class KeyInput:
    """
    Class that ease the use of key input when the user need to enter something.
    """
    
    def __init__(self, pel, mode='y/n'):
        self.mode=mode
        self.pel=pel
        
    def log_err(self, msg):
        self.pel.err(msg) #Now we directly write an error in the log (and increment error count)
        
    def parse_yn(self,inp,ermsg):
        if inp.find("yes") != -1 or inp.find("y") != -1:
            return True
    
        if inp.find("no") != -1 or inp.find("n") != -1:
            self.log_err(ermsg)
            return False
    
    def get_yesno(self,question, ermsg=""):
        inp = raw_input(question+" ["+self.mode+"]:")
        while True:
            if inp.find("yes") != -1 or inp.find("y") != -1:
                return True
    
            if inp.find("no") != -1 or inp.find("n") != -1:
                self.log_err(ermsg)
                return False
    
            inp = raw_input('Enter "yes" or "no" to continue:')
            
    def get_yesnotimout(self,question,tout=10,ermsg=""):
        inp = raw_input(question+" ["+self.mode+"]  (timeout="+tout+" s):")
        print inp
        i, o, e = select.select( [sys.stdin], [], [], tout )
        if not i:
            self.log_err("Warning: timeout %s", question)
        else:
            self.parse_yn(sys.stdin.readline().strip(),ermsg)
            
    def get_nonblockkey(self,char):
        old_settings = termios.tcgetattr(sys.stdin)
        try: 
            tty.setcbreak(sys.stdin.fileno()) 
            i, o, e = select.select( [sys.stdin], [], [], 0)
            if i:
                c= sys.stdin.read(1)
                print "%s %x" %(c,c)
                if c==char: return True
        finally: 
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return False
        
    
    def bit_indep(self,question,_func,check):
        #While loop to check each bit independently
        print "not define"
            
    def msg_cont(self,msg):
        raw_input(msg + ": Press any key to continue...")
        
        
class BitManip:
    """
    Class that with static method do ease bit-wise manipulation 
    """
    
    @staticmethod
    def inv_b32(data):
        return c_uint(~data).value
    
    @staticmethod
    def inv_b16(data):
        return c_ushort(~data).value
    
    @staticmethod
    def inv_b8(data):
        return c_ubyte(~data).value
   
    @staticmethod
    def get_binstr(data,sep=" ",modsep=8):
        txt=""
        for i in range(0,32):
            i=31-i
            if i % modsep==0: sep2=sep
            else: sep2=""
            txt+="%d%s" %(((data >> i) & 1),sep2)
        return txt
    
    @staticmethod
    def swap32(x):
        return (((x << 24) & 0xFF000000) |
            ((x <<  8) & 0x00FF0000) |
            ((x >>  8) & 0x0000FF00) |
            ((x >> 24) & 0x000000FF))
    
