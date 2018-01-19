#!   /usr/bin/env   python
#    coding: utf8
'''
Class that provides an interactive shell for the VUART_bridge driver.

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
import re
import sys
import time
import select
import datetime as dt
# User defined modules
from bridges.VUART_bridge import VUART_bridge
from gendrvr import BusCritical, BusWarning
from p7sException import p7sException, Retry, Error
from ewberrno import Ewberrno

class VUART_shell():
    '''
    This class provides an interactive shell to handle the VUART_bridge driver.

    It adds an abstraction layer over the VUART driver in order to show the user
    an interface like when connected through serial connection. It provides
    an interactive shell with a prompt where the user could insert the WRPC commands.

    Interactive commands (such as gui or stat cont) keeps the "ESC" key to stop
    the data output from the device. The shell can be closed using the key
    combination "ctrl-q".
    '''
    ## Build date for the min version of firmware supported
    VER_MIN_DATE = dt.datetime(2015, 10, 29, 0, 0)

    # Regular expresions for parsing the stat cmd

    # Get the IP
    IP_REGEX = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    # Get the WR mode
    MODE_REGEX = '[a-zA-Z]+_[a-zA-Z]+_[a-zA-Z]+'
    # Get the temp value
    TEMP_REGEX = '\d{1,3}\.\d{4}'
    # Get the servo state
    SERVO_REGEX = 'ss:\'\w*\''
    # Get TAI Time (from "time" command)
    TIME_REGEX = '^\w{3}.*\w{3}.*\d+.*\d{4}.*\d{2}:\d{2}:\d{2}'
    # Get Link, RX, TX y lock of each WR port (append wrX at the begining of the regexp)
    PORT_REGEX = '.*lnk:(\d).*rx:(\d+).*tx:(\d+).*lock:(\d+)'
    INDEX_LNK = 1
    INDEX_RX = 2
    INDEX_TX = 3
    INDEX_LOCK = 4
    # Get servo state
    SS_REGEX = 'ss:\'(\w+)\''
    # Get sync source
    SYNCS_REGEX = 'syncs:(wr\d{1})'
    # Get Round-trip time
    RTT_REGEX = 'mu:(\d+)'
    # Get Master-slave delay
    MSDEL_REGEX = 'dms:(\d+)'
    # Get Master PHY delays
    MPHYDEL_REGEX = 'dtxm:(\d+).*drxm:(\d+)'
    # Get Slave PHY delays
    SPHYDEL_REGEX = 'dtxs:(\d+).*drxs:(\d+)'
    # Get total link asymmetry (it could be a negative number)
    ASYM_REGEX = 'asym:(.?\d+)'
    # Get rtt delay
    CRTT_REGEX = 'crtt:(\d+)'
    # Get clock offset
    CKO_REGEX = 'cko:(.?\d+)'
    # Get phase setpoint
    PSETP_REGEX = 'setp:(\d+)'


    def __init__(self, ip, verbose=False):
        '''
        Constructor

        Args:
            ip (str) : IP direction for the device
            verbose (bool) : Enables verbose output

        Raises:
            ConsoleError : When the specified device fails opening.
        '''
        self.vuart = VUART_bridge("eth", ip, verbose)
        attemps = 3
        cur = 0
        while True:
            try:
                self.vuart.open()
                break
            except BusWarning as e:
                if cur >= attemps:
                    raise e
                print("The desired device cannot be connected, retrying...")
                cur += 1

        self.vuart.flushInput()
        self.ver_date = None
        self.gui_enabled = False
        self.refresh = 5  # Refresh time for interactive commands (1 sec)
        ver = self.vuart.sendCommand("ver")
        self.__get_firm_date__(ver.decode('utf8', errors='ignore'))

        # Compile regular expresions
        self.mode_regex = re.compile(self.MODE_REGEX)
        self.time_regex = re.compile(self.TIME_REGEX)
        self.wr0_regex = re.compile("%s%s" % ("wr0", self.PORT_REGEX))
        self.wr1_regex = re.compile("%s%s" % ("wr1", self.PORT_REGEX))
        self.ip_regex = re.compile(self.IP_REGEX)
        self.syncs_regex = re.compile(self.SYNCS_REGEX)
        self.rtt_regex = re.compile(self.RTT_REGEX)
        self.msdel_regex = re.compile(self.MSDEL_REGEX)
        self.mphydel_regex = re.compile(self.MPHYDEL_REGEX)
        self.sphydel_regex = re.compile(self.SPHYDEL_REGEX)
        self.asym_regex = re.compile(self.ASYM_REGEX)
        self.crtt_regex = re.compile(self.CRTT_REGEX)
        self.cko_regex = re.compile(self.CKO_REGEX)
        self.psetp_regex = re.compile(self.PSETP_REGEX)
        self.ss_regex = re.compile(self.SS_REGEX)

    def __secure_sendCommand__(self, cmd, retry=3):
        '''
        Wrapper for the VUART_bridge.sendCommand

        This method will retry a call to the driver if any issue was occured.

        Args:
            cmd (str) : The command for the WR device
            retry (int) : How many times repeat a failed call to the driver

        Returns:
            The response of the command passed (if any)

        Raises:

        '''
        attempts = 0

        while True:
            try:
                ret = self.vuart.sendCommand(cmd)
                return ret
            except BusWarning as e:
                if attempts >= retry:
                    raise Error(Ewberrno.EIO , "Too many errors executing the command %s" % cmd)
                else:
                    attempts += 1
                if attempts == 1: print ("The connection seems to be lost. Retrying...")

    def __get_firm_date__(self, raw_ver):
        '''
        Private method to fill the firmware build date

        Args:
            raw_ver (str) : Raw output from "ver" command
        '''
        date_pattern = 'Built on [a-zA-Z]{3} \d{1,2} \d{4}'
        date_regex = re.compile(date_pattern)

        m = date_regex.search(raw_ver)
        if m is None:
            self.gui_enabled = False
            return

        date_regex = re.compile(date_pattern[9:])
        ret = date_regex.search(m.group())
        self.ver_date = dt.datetime.strptime(ret.group(), "%b %d %Y")

        if self.ver_date >= self.VER_MIN_DATE:
            self.gui_enabled = True
        else:
            self.gui_enabled = False

    def __format_gui__(self, stat, time):
        '''
        Private method to format an output as the WRPC GUI does.

        ONLY compatible for WR Core build e261d79-dirty or newer

        Args:
            stat (str) : Raw data from stat command
            time (str) : Raw data from time command
        '''
        sync_info_valid = 2
        raw = stat.decode('utf8')
        time =  time.decode('utf8')
        board_mode = self.mode_regex.search(raw).group(0)

        if board_mode is None:
            raise Error(p7sException.err[Ewberrno.ENODEV], "Could not retrieve mode from WR-LEN")

        wr0 = self.wr0_regex.search(raw)
        wr1 = self.wr1_regex.search(raw)
        if wr0 is None or wr1 is None:
            print("\n")
            return

        wr0_enable = wr0.group(1) == '1'
        wr1_enable = wr1.group(1) == '1'

        sys.stdout.write("\033[94;1mWR PTP Core Sync Monitor: PPSI - WRLEN\033[0m\n")
        sys.stdout.write("\033[2mEsc = ctrl-c\033[0m\n\n")
        sys.stdout.write("\033[94mTAI time:\033[0m            \033[1m%s\033[0m\n\n" %\
        self.time_regex.search(time).group(0))
        sys.stdout.write("\033[1;92mWR-LEN mode : \033[1m%s\033[0m\n\n" % board_mode)
        sys.stdout.write("\033[94;1mLink status:\033[0m\n\n")

        # Removed to save time
        # ip_raw = self.vuart.sendCommand("ip")
        # ip = self.ip_regex.search(ip_raw.decode('utf8'))
        #
        # sys.stdout.write("\033[1mIPv4:\033[0m%s\033[92m\033[0m\n\n" % (ip))

        # mode = self.vuart.sendCommand("mode")
        try:
            mode = self.__secure_sendCommand__("mode")
        except Error as e:
            raise e

        # Port wr0 info
        if wr0_enable:
            m = "WR Master" if mode == "master" or mode == "slave_wr1" else "WR Slave"
            sys.stdout.write("\033[1mwr0 :\033[92m Link up  \033[0m\033[2m(RX: %s, TX: %s), mode: \033[0m\033[1m%s \033[0m\033[1;92m%s\033[0m\n\n" %\
            (wr0.group(self.INDEX_RX), wr0.group(self.INDEX_TX), m,"Locked" if wr0.group(self.INDEX_LOCK)=="1" else "Link down"))
        else:
            sys.stdout.write("\033[1mwr0 : \033[1;31mLink down\033[0m\n\n")
            sync_info_valid -= 1

        # Port wr1 info
        if wr1_enable:
            m = "WR Master" if mode == "master" or mode == "slave_wr0" else "WR Slave"
            sys.stdout.write("\033[1mwr1 :\033[92m Link up  \033[0m\033[2m(RX: %s, TX: %s), mode: \033[0m\033[1m%s \033[0m\033[1;92m%s\033[0m\n\n" %\
            (wr1.group(self.INDEX_RX), wr1.group(self.INDEX_TX), m,"Locked" if wr1.group(self.INDEX_LOCK)=="1" else "Link down"))
        else:
            sys.stdout.write("\033[1mwr1 : \033[1;31mLink down\033[0m\n\n")
            sync_info_valid -= 1

        show_fail = False
        if sync_info_valid >= 1:
            rtt = self.rtt_regex.search(raw)
            if rtt == None:
                show_fail = True
            else :
                ss = self.ss_regex.search(raw).group(1)
                syncs = self.syncs_regex.search(raw).group(1)

                sys.stdout.write("\033[1mServo state:             %s\033[0m\n" % ss)
                sys.stdout.write("\033[1mSynchronization source:  %s\033[0m\n\n" % syncs)

                sys.stdout.write("\033[34mTiming parameters:\033[0m\n\n")
                rtt = rtt.group(1)
                sys.stdout.write("\033[2mRound-trip time (mu):    \033[0m\033[1;97m%s ps\033[0m\n" % rtt)

                msdel = self.msdel_regex.search(raw).group(1)
                sys.stdout.write("\033[2mMaster-slave delay:      \033[0m\033[1;97m%s ps\033[0m\n" % msdel)

                mphydel_tx = self.mphydel_regex.search(raw).group(1)
                mphydel_rx = self.mphydel_regex.search(raw).group(2)
                sys.stdout.write("\033[2mMaster PHY delays:       \033[0m\033[1;97mTX: %s ps, RX: %s ps\033[0m\n" %\
                (mphydel_tx, mphydel_rx))

                sphydel_tx = self.sphydel_regex.search(raw).group(1)
                sphydel_rx = self.sphydel_regex.search(raw).group(2)
                sys.stdout.write("\033[2mSlave PHY delays:        \033[0m\033[1;97mTX: %s ps, RX: %s ps\033[0m\n" %\
                (sphydel_tx, sphydel_rx))

                asym = self.asym_regex.search(raw).group(1)
                sys.stdout.write("\033[2mTotal Link asymmetry:    \033[0m\033[1;97m%s ps\033[0m\n" % asym)

                crtt = self.crtt_regex.search(raw).group(1)
                sys.stdout.write("\033[2mCable rtt delay:         \033[0m\033[1;97m%s ps\033[0m\n" % crtt)

                cko = self.cko_regex.search(raw).group(1)
                sys.stdout.write("\033[2mClock offset:            \033[0m\033[1;97m%s ps\033[0m\n" % cko)

                psetp = self.psetp_regex.search(raw).group(1)
                sys.stdout.write("\033[2mPhase setpoint:          \033[0m\033[1;97m%s ps\033[0m\n" % psetp)

                sys.stdout.write("\033[2mUpdate interval:         \033[0m\033[1;97m%.1f sec\033[0m\n" % self.refresh)
        elif sync_info_valid < 2 or show_fail:
            sys.stdout.write("\033[1;31mMaster mode or sync info not valid\033[0m\n\n")

    def run(self):
        '''
        Open the interactive shell
        '''
        self.vuart.flushInput()
        sys.stdout.write("\033[1m\nVirtual UART shell for the White Rabbit LEN board\033[0m (v1.0)\n\n")
        self.print_stats()
        sys.stdout.write("Type \033[1m_help\033[0m to show the help info\n\n")

        while(True):
            sys.stdout.write("\033[1mwrc# \033[0m")
            cmd = str(raw_input())
            if cmd == "_exit" :
                print("Bye!")
                exit(0)
            elif cmd == "_help"     : self.help()

            elif "_load" in cmd     :
                params = cmd.split(" ")
                if len(params) < 2:
                    print("Use : _load <filein> [<fileout>]")
                    continue
                try:
                    fin = open(params[1],'r')
                    fout = open(params[2],'a+') if len(params) > 2 else None
                    self.run_script(fin, fout)
                    fin.close()
                    if len(params) > 2: fout.close()
                except Exception as e:
                    print e

            elif "_refresh" in cmd  :
                param = cmd.split(" ")
                if len(param) < 2:
                    print("Actual : %.2f secs" % (self.refresh))
                    print("To change it, call '_refresh' with a value (> 1.5)")
                    print("Refresh rates lower than 3 secs are not advisable")
                    continue
                self.set_refresh(float(param[1]))
            elif cmd == "_ver"      : self.ver_info()
            elif cmd == "gui" or "stat cont" in cmd:
                self.run_interactive(cmd)
            else:
                # ret = self.vuart.sendCommand(cmd)
                try:
                    ret = self.__secure_sendCommand__(cmd,4)
                except Error as e:
                    sys.stdout.write("\033[1;31mError:\033[0mConnection with the WR-LEN is lost\n")
                    print ("See the manual for more deatils")
                    exit(1)
                if ret == "" : continue
                else: print ret

    def run_script(self, script, saveto=None):
        '''
        Execute a bunch of WRPC commands.

        Gui or stat cont are not allowed commands for this mode of execution.

        Args:
            script (file) : An instance of an opened file
            saveto (file) : If a file is passed, the output of the executed commands will be saved to it.
        '''
        if script is None:
            print("Not opened file")
            return

        print("Running script...")

        if not saveto is None:
            saveto.write("Output generated on %s\n\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M")))

        for line in script:
            if "gui" in line or "stat cont" in line:
                print ("Not allowed command %s" % (line))
                continue
            # ret = self.vuart.sendCommand(line)
            try:
                ret = self.__secure_sendCommand__(line[:-1]) # Don't forget: read lines from file end in '\n'
            except Error as e:
                sys.stdout.write("\033[1;31mError:\033[0mConnection with the WR-LEN is lost\n")
                print ("See the manual for more deatils")
                return

            if saveto is not None:
                saveto.write("@%s\n" % line[:-1])
                saveto.write("%s\n\n" % ret)
            time.sleep(0.5)
        if saveto is not None:
            saveto.write("\n\n")

    def run_interactive(self, cmd):
        '''
        Special method for handling special WRPC interactive commands as GUI or STAT CONT

        Args:
            cmd (str) : gui or stat cont n
        '''
        if cmd == "gui" and not self.gui_enabled:
            print("The command 'gui' is not available. Type '_ver' to see more details")
            return

        # Help info for the user
        print("Entering in interactive mode. Press 'ctrl-c' to exit")
        time.sleep(2.5)
        sys.stdout.write("\x1b[2J\x1b[H")

        try:
            if cmd == "gui":
                while True:
                    try:
                        raw_stat = self.vuart.sendCommand("stat")
                        raw_time = self.vuart.sendCommand("time")
                    except Error as e:
                        sys.stdout.write("\033[1;31mError:\033[0mConnection with the WR-LEN is lost\n")
                        print ("See the manual for more deatils")
                        return
                    self.__format_gui__(raw_stat, raw_time)
                    time.sleep(self.refresh)
                    sys.stdout.write("\x1b[2J\x1b[H")

            elif "stat" in cmd:
                sys.stdout.write("\033[1mRefresh rate : %.2f secs\033[0m\n\n" % self.refresh)
                while True:
                    try:
                        ret = self.vuart.sendCommand(cmd)
                    except Error as e:
                        sys.stdout.write("\033[1;31mError:\033[0mConnection with the WR-LEN is lost\n")
                        print ("See the manual for more deatils")
                        return
                    print(ret)
                    self.vuart.flushInput()
                    time.sleep(self.refresh)

        except KeyboardInterrupt:
            sys.stdout.write("\033[0mExiting...\n")
            return

    def ver_info(self):
        '''
        Method to print info about enabled capabilites of the VUART"
        '''
        if not self.gui_enabled:
            print("The firmware version of the WR-LEN does not fully support the Virtual UART capabilities")
            print("The following WRPC commands are not available:")
            print("-> gui")
        else:
            print("The firmware version of the WR-LEN fully supports the Virtual UART capabilities")

    def print_stats(self):
        '''
        Method to print some info about the device and connection established
        '''
        try:
            ver = self.vuart.sendCommand("ver")
        except Error as e:
            sys.stdout.write("\033[1;31mError:\033[0mConnection with the WR-LEN is lost\n")
            print ("See the manual for more deatils")
            exit(1)
        sys.stdout.write("\033[1m\nBoard info:\033[0m\n\n")
        print("%s\n\n" % (ver))

    def set_refresh(self, value):
        '''
        Method to change the refresh interval for interactive commands

        Args:
            value (float) : Refresh interval (must be greater than 1.5 sec)
        '''
        if value < 1.5:
            print("Refresh rate not changed. The value must be greater than 1.5 secs")
        else:
            self.refresh = value

    def help(self):
        '''
        Show some info about the use of the shell
        '''
        print("""
Special commands (not for the device, "_" preceding those commands):\n
· _help : Prints this help
· _ver  : Prints useful info about board version
· _exit : Exits the shell
· _load <filein> [<fileout>]: Loads an input file with WRPC commands
· _refresh <value> : Change refresh interval. The value must be greater than 1.5 secs.
Any other commands will be passed directly to the WR-LEN device.""")
