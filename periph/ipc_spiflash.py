#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
This File contains the SpiFlash class for programming a SPI Flash memory remotely through Etherbone

@file
@date Created on Jun 29, 2015
@author Husein Gomiz (hgomiz<AT>sevensols.com)
@author Benoit Rat (benoit<AT>sevensols.com)
@copyright LGPL v2.1
@see http://www.ohwr.org
@see http://www.sevensols.com
@ingroup periph
'''

import time
import sys

class SpiFlash:
    """
    SpiFlash class

    This class is used for programming a SPI Flash memory remotely through Etherbone
    """

    #Registers Offsets
    CR_offset=0x0       #Control Register
    SR_offset=0x4       #Status Register
    DR_offset=0x8       #Data Register
    FSR_offset=0xc      #FIFO Status Register
    IIR_offset=0x10     #ICAPE2 Input Register
    IOR_offset=0x14     #ICAPE2 Output Register
    ICR_offset=0x18     #ICAPE2 Control Register
    RWC_offset=0x1C     #Received word counter

    #Operation Modes
    mod_RESET=0x0
    mod_UPDATE=0x1
    mod_CIDO=0x3
    mod_VO=0x5

    #Masks
    #CR
    msk_RE=0x1          #Reset_Enable
    msk_CIDO=0x2        #CheckIdOnly
    msk_VO=0x4          #VerifyOnly

    #SR
    msk_PSWOK=0x8000    #ProgramSwitchWordOK
    msk_VOK=0x4000      #VerifyOK
    msk_POK=0x2000      #ProgramOK
    msk_EOK=0x1000      #EraseOK
    msk_ESWOK=0x800     #EraseSwitchWordOK
    msk_CIDOK=0x400     #CheckIdOK
    msk_IOK=0x200       #InitializeOK
    msk_ST=0x100        #Started
    msk_ECRC=0x80       #ErrorCrc
    msk_ETO=0x40        #ErrorTimeOut
    msk_EP=0x20         #ErrorProgram
    msk_EE=0x10         #ErrorErase
    msk_EID=0x8         #ErrorIdcode
    msk_ERR=0x4         #Error
    msk_DN=0x2          #Done
    msk_RB=0x1          #Ready_Busy

    #FSR
    msk_RST_N=0x80000000 #RESET FIFO Active low reset
    msk_WF=0x200        #Write Full
    msk_FSR_RE=0x100    #Read Empty
    msk_WC=0xFF         #Write Count

    ERASE_TO=50         #Maximun number of seconds to check timeout
    ENDPRGM_TO=10       #Maximun number of seconds to check end programs

    FIFO_WSIZE=256
    PKTWORDS=FIFO_WSIZE/2 #We are sending packets of 128 words because the FIFO has 256 words

    def __init__(self,bus,baseFlash,debug=False):
        """__init__ method

        Args:
            bus (EthBone) : Communication bus
            baseFlash (int) : Base address for the WB-SPI-Flash-Update
            debug(bool): Boolean seting debug mode if True
        """

        self.baseFlash = baseFlash
        self.bus = bus
        self.debug=debug

    def flash_update(self,mode,mcs_file):
        '''Main Method for starting the SPI Flash operation

        This method resets the needed modules,sets the operation mode and calls the methods to perform it.

        Args:
            mode: There is three possible operation modes:
                * cido: check id
                * vo: verification
                * update: perform all the procedure
            mcs_file: in case the mode is "update" we must provide the mcs_file that we want to upload
        '''

        self.mode=mode

        #reset Flash Programmer
        self.resetFlash()

        #Reset FIFO
        self.resetFifo()

        if self.mode=="cido":
            self.cidoMode()
        elif self.mode=="vo":
            self.voMode()
        elif self.mode=="update":
            self.updateMode(mcs_file)
        else:
            print "Not a valid Mode"

    def resetFlash(self):
        '''Method for reseting the Flash memory
        '''
        self.bus.devwrite( 0, self.baseFlash+self.CR_offset, 4, self.mod_RESET)

    def setFlashMode(self):
        '''Method for seting the operation mode of the SpiFlashProgrammer
        '''
        if self.mode=="cido":
            self.bus.devwrite( 0, self.baseFlash+self.CR_offset, 4, self.mod_CIDO)
        elif self.mode=="vo":
            self.bus.devwrite( 0, self.baseFlash+self.CR_offset, 4, self.mod_VO)
        elif self.mode=="update":
            self.bus.devwrite( 0, self.baseFlash+self.CR_offset, 4, self.mod_UPDATE)

    def resetFifo(self):
        '''Method for resetting the FIFO
        '''
        self.bus.devwrite( 0, self.baseFlash+self.FSR_offset, 4, 0x00000000)
        self.bus.devwrite( 0, self.baseFlash+self.FSR_offset, 4, 0x80000000)

    def cidoMode(self):
        '''Method for performing the Check ID Only operation
        '''
        print "Check ID Only mode"
        self.setFlashMode()
        self.endFlash()

    def voMode(self):
        '''Method for performing the Verify Only operation
        '''
        print "Verify Only mode"
        self.setFlashMode()
        self.endFlash()

    def SR_to_str(self,status_reg=None):
            if status_reg==None:
                status_reg=self.bus.read(self.baseFlash+self.SR_offset)
            desc= [""] * 32
            desc[0]="READY_BUSY"
            desc[1]="DONE"
            desc[2]="ERR"
            desc[3]="ERR_IDCODE"
            desc[4]="ERR_ERASE"
            desc[5]="ERR_PROGRAM"
            desc[6]="ERR_TIMEOUT"
            desc[7]="ERR_CRC"
            desc[8]="STARTED"
            desc[9]="InitializeOK"
            desc[10]="CheckIDOK"
            desc[11]="EraseSwitchWordOK"
            desc[12]="EraseOK"
            desc[13]="ProgramOK"
            desc[14]="VerifyOK"
            desc[15]="ProgramSwicthWordOK"
            msg="REG_SR=0x%08x : " %(status_reg)
            for pos,val in enumerate(desc):
                if status_reg & (1 << pos):
                    msg=msg+val+", "
            return msg[:-2]

    def updateMode(self,mcs_file):
        '''Method for performing the Update operation
        '''
        print "UPDATE mode"

        f = open(mcs_file, "rb")
        lines=f.readlines()

        #this function selects the useful lines, extracts the 32 bit data from each of those lines and returns a list of packets
        #of 128 words of 32 bits.
        flash_packets=[]
        self.linesToPackets(lines,flash_packets)

        if self.debug:
            print "packets:", len(flash_packets)
            print "len last paket", len(flash_packets[-1])

        self.setFlashMode()
        self.eraseFlash()
        self.programFlash(flash_packets)
        try:
            self.endFlash()
        except Exception, e:
            wc=self.bus.read(self.baseFlash+self.RWC_offset)
            print "Received words=%d (0x%08x), expected=%d" % (wc,wc,(len(flash_packets)-1)*self.PKTWORDS+len(flash_packets[-1]))
            raise


    def eraseFlash(self):
        '''Method that checks the development of the Flash memory erasure
        '''
        # wait for Erase OK
        print "Erasing ",

        status_reg=self.bus.read(self.baseFlash+self.SR_offset)
        EOK=(self.msk_EOK & int(status_reg))
        ERROR=(self.msk_ERR & int(status_reg))
        old_SR=status_reg
        count=0
        while EOK==0 and ERROR==0:
            status_reg=self.bus.read(self.baseFlash+self.SR_offset)
            EOK=(self.msk_EOK & int(status_reg))
            if self.debug:
                new_SR=self.bus.read(self.baseFlash+self.SR_offset)
                if new_SR != old_SR:
                    print self.SR_to_str(new_SR)
                    old_SR=new_SR
            if count > self.ERASE_TO:
                raise  NameError('Timeout while erasing SPI (> %d s)' % (self.ERASE_TO))
            time.sleep(1)
            count=count+1
            sys.stdout.write(".")
            sys.stdout.flush()
        if EOK and self.debug:
            print "Erase OK"
        elif self.debug:
            print "Erase Failed"


    def programFlash(self,flash_packets):
        '''Method for sending the update data to the Flash memory
        '''
        j= 0
        print " Programming ",
        status_reg=self.bus.read(self.baseFlash+self.SR_offset)
        POK=(self.msk_POK & int(status_reg))
        ERROR=(self.msk_ERR & int(status_reg))
        old_SR=status_reg & 0xfffe                  #ready_busy switch is not interesting
        self.bus.wrcr=0
        while POK==0 and ERROR==0:
            #Check Writing Done
            status_reg=self.bus.read(self.baseFlash+self.SR_offset)
            POK=(self.msk_POK & int(status_reg))
            ERROR=(self.msk_ERR & int(status_reg))
            #Check FIFO
            FIFO_status_reg=self.bus.read(self.baseFlash+self.FSR_offset)
            FCount=(self.msk_WC & int(FIFO_status_reg))
            if (FCount < self.PKTWORDS):
                if j<len(flash_packets):
                    self.bus.devblockwrite(0, self.baseFlash+self.DR_offset, flash_packets[j],0x0)
                    time.sleep(0.001) #Sleep 1 milliseconds to avoid charging the network
                    j=j+1
                    if j%100==0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                elif (j>len(flash_packets)):
                    raise  NameError('ERROR: Overflowing packets (%d > %d s)' % (j,len(flash_packets)))

                elif j==len(flash_packets):
                    break

        if self.debug:
            print "Programming Finished (CRC=0x%08x)" %(self.bus.wcrc & 0xFFFFFFFF)
            print "Packets Written:", j

    def endFlash(self):
        '''Method for finishing the operation, regardless of the operation mode.

        If performing Update operation the board is Rebooted at the end runing IPROG_reboot
        '''
        if self.debug:  print "Waiting DONE... %s" %(self.SR_to_str())
        status_reg=self.bus.read(self.baseFlash+self.SR_offset)
        DONE=(self.msk_DN & int(status_reg))
        old_SR=status_reg
        count=0
        while DONE==0:
            status_reg=self.bus.read(self.baseFlash+self.SR_offset)
            DONE=(self.msk_DN & int(status_reg))
            if status_reg != old_SR:
                if self.debug:  print self.SR_to_str()
                old_SR=status_reg
                count=0
            if count > self.ENDPRGM_TO:
                raise  NameError('Timeout while waiting DONE > %d s (%s)' % (self.ENDPRGM_TO,self.SR_to_str()))
            time.sleep(1)
            count=count+1
        print " DONE"
        if self.debug:
            print self.SR_to_str()

        ERROR=(self.msk_ERR & int(status_reg))
        PSWOK=(self.msk_PSWOK & int(status_reg))

        if ERROR:
            raise NameError("An error was detected %s" % (self.SR_to_str(status_reg & 0xF8)))

        if PSWOK:
            print "REBOOTING"
            self.IPROG_reboot()


    def IPROG_reboot(self):
        '''Method for rebooting the board

        This sequence performs IPROG through ICAPE2. The commands are bit swapped
        '''

        iprog_comm=[]
        iprog_comm.append(self.swap(0xffffffff))    #Dummy Word
        iprog_comm.append(self.swap(0xAA995566))    #Sync Word
        iprog_comm.append(self.swap(0x20000000))    #Type 1 NO OP
        iprog_comm.append(self.swap(0x30020001))    #Type 1 Write 1 Words to WBSTAR
        iprog_comm.append(self.swap(0x00000000))    #Warm Boot Start Address (Load the Desired Address)
        iprog_comm.append(self.swap(0x30008001))    #Type 1 Write 1 Words to CMD
        iprog_comm.append(self.swap(0x0000000F))    #IPROG_reboot Command
        iprog_comm.append(self.swap(0x20000000))    #Type 1 NO OP

        old_silent=self.bus.silent;
        self.bus.silent=True ##Force Silent when reprogramming
        self.bus.devblockwrite(0, self.baseFlash+self.IIR_offset, iprog_comm,0x0)
        self.bus.silent=old_silent;

    def swap(self,nsWord):
        '''Method for bit swapping a 32 bit word
        '''
        sWord=0

        sWord=sWord | (nsWord<<(7) &  0x80808080)
        sWord=sWord | (nsWord<<(5) &  0x40404040)
        sWord=sWord | (nsWord<<(3) &  0x20202020)
        sWord=sWord | (nsWord<<(1) &  0x10101010)
        sWord=sWord | (nsWord>>(7) &  0x01010101)
        sWord=sWord | (nsWord>>(5) &  0x02020202)
        sWord=sWord | (nsWord>>(3) &  0x04040404)
        sWord=sWord | (nsWord>>(1) &  0x08080808)

        return sWord

    def linesToData(self,lines_list,data_lines):
        """ This method takes the lines from the mcs file and extracts the useful data

        Returns a list of lines once removed start code, byte count, address, record type, checksum...
        only the useful data is left
        """

        for i in range(0,len(lines_list)-1):                         #the last line is left untouched as it is the checksum
            record_type=int(lines_list[i][7:9],16)                   #two hex digits indicating the record type
            if record_type==0:                                       # DATA type
                mod_line= lines_list[i][9:len(lines_list[i])-3]      #take away the first 10 hex digits and the last 3
                data_lines.append(mod_line)
        return data_lines

    def linesToPackets(self,lines,flash_packets):
        """Method for packing a list of lines of a MCS file into a list of packets of words

        This method extract four 32 bit words for each usefull line of the mcs file and packs it in packets of 128 words of 32 bits
        """

        #lines once removed start code, byte count, address, record type, checksum...
        #only the 32 bit useful data is left
        data_lines=[]
        self.linesToData(lines,data_lines)

        # turn the Data lines strings into byte arrays
        bytearray_lines=[]
        self.bus.dataToByteArray(data_lines,bytearray_lines)

        # create a single list with all the  bytes
        bytes_list=[]
        for sublist in bytearray_lines:
            for val in sublist:
                bytes_list.append(val)

        #for j in range(-10,0):
        #    print "0x%02x" % bytes_list[j]


        # Group the bytes into 4 Bytes words
        flash_words=[]
        for j in range(0,len(bytes_list),4):
            if (j<len(bytes_list)-(len(bytes_list)%4)):
                tmpWord= (bytes_list[j]<<24 | bytes_list[j+1] << 16 | bytes_list[j+2] << 8 | bytes_list[j+3])
                flash_words.append(tmpWord)
                #if j>(len(bytes_list)-4*10): print "@x%03x: 0x%08x" %(j, flash_words[-1] & 0xFFFFFFFF)

            #the last word is completed with 0xee if needed
            else:
                if len(bytes_list)%4==3:
                    last_word=(bytes_list[j]<<24 | bytes_list[j+1] << 16 | bytes_list[j+2] << 8 | 0xee)
                elif len(bytes_list)%4==2:
                    last_word=(bytes_list[j]<<24 | bytes_list[j+1] << 16 | 0xee << 8 | 0xee)
                elif len(bytes_list)%4==1:
                    last_word=(bytes_list[j]<<24 | 0xee << 16 | 0xee << 8 | 0xee)
                flash_words.append(last_word)
                #print "@x%03x: 0x%08x" %(j, flash_words[-1] & 0xFFFFFFFF)


        # the 4 bytes words are grouped in self.PKTWORDS words packets
        self.bus.wordsToPackets(flash_words,flash_packets,self.PKTWORDS)

        if self.debug:
            print "lines:", len(lines)
            print "Data lines:", len(data_lines)
            print "Byte Arrays:", len(bytearray_lines)
            print "Bytes:",len(bytes_list)
            print "words:", len(flash_words)

        return flash_packets


    def eb_sw_loader(self,RAM_file,RAM_offset=0x0,SYSCON_offset=0x30400,pktwords=256):
        '''
        Method for loading new SW to the LM32 soft processor

        Args:
            RAM_file: The .ram file with the LM32 firmware
            RAM_offset: The offset of WB4-BlockRAM in the WB bus
            SYSCON_offset: The offset of WR-Periph-Syscon in the WB bus
            pktwords: Number of words to send by packet (< MAXBYTE_PAYLOADPKT/4)

        Returns:
            0 if everything was OK, 1 otherwise
        '''

        f = open(RAM_file, "rb")
        lines=f.readlines()
        #extract the valid data from the RAM file
        data_lines=[]
        for i in range(0, len(lines)):
            tmp_line=lines[i][len(lines[i])-9:len(lines[i])-1]
            data_lines.append(tmp_line)
        print data_lines[1]

        #Convert from str to int
        int_lines=[]
        for i in range(0, len(data_lines)):
            tmp_line=int(data_lines[i],16)
            int_lines.append(tmp_line)
        #from lines to 128 word packets
        data_packets=[]
        self.bus.wordsToPackets(int_lines, data_packets,pktwords)
        #disable the processor
        self.bus.devwrite(0, SYSCON_offset, 4, 0x1deadbee)
        #Write the new sw at the ram memory
        for i in range(0,len(data_packets)):
            self.bus.devblockwrite(0, RAM_offset+(4*i*pktwords), data_packets[i], 0x4)
            #check written RAM
            #FIXME: do this with devblockread
            rbdata_list=[]
            #for j in range(0,len(data_packets[i])):
                #rbdata=self.bus.devread(0, RAM_offset+4*i*pktwords+4*j, 4)
                #rbdata_list.append(rbdata)
            #fwLoad_er=self.cmpList(rbdata_list,data_packets[i])
            #if fwLoad_er:
                #return 1
        #enable the processor
        self.bus.devwrite(0, SYSCON_offset, 4, 0x0deadbee)
        return 0

    def cmpList(self,list1,list2):
        '''Method for comparing two lists
        '''

        error=False
        if len(list1) != len(list2):
            print "Different list sizes", len(list1) , len(list2)
        else:
            for i in range(0,len(list1)):
                if list1[i]!=list2[i]:
                    error=True
                    break
        return error
