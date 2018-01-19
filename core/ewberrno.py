#!   /usr/bin/env   python
# -*- coding: utf-8 -*
'''
Custom exceptions

@file
@date Created on Sep 28, 2015
@author Fran Romero
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

EXTERNAL_DEF = 1

class Ewberrno:

    # Standard errno system symbols borrowed from linux/include/errno.h
    EPERM = 1  # Operation not permitted
    ENOENT = 2  # No such file or directory
    ESRCH = 3  # No such process
    EINTR = 4  # Interrupted system call
    EIO = 5  # I/O error
    ENXIO = 6  # No such device or address
    E2BIG = 7  # Arg list too long
    ENOEXEC = 8  # Exec format error
    EBADF = 9  # Bad file number
    ECHILD = 10  # No child processes
    EAGAIN = 11  # Try again
    ENOMEM = 12  # Out of memory
    EACCES = 13  # Permission denied
    EFAULT = 14  # Bad address
    ENOTBLK = 15  # Block device required
    EBUSY = 16  # Device or resource busy
    EEXIST = 17  # File exists
    EXDEV = 18  # Cross-device link
    ENODEV = 19  # No such device
    ENOTDIR = 20  # Not a directory
    EISDIR = 21  # Is a directory
    EINVAL = 22  # Invalid argument
    ENFILE = 23  # File table overflow
    EMFILE = 24  # Too many open files
    ENOTTY = 25  # Not a typewriter
    ETXTBSY = 26  # Text file busy
    EFBIG = 27  # File too large
    ENOSPC = 28  # No space left on device
    ESPIPE = 29  # Illegal seek
    EROFS = 30  # Read-only file system
    EMLINK = 31  # Too many links
    EPIPE = 32  # Broken pipe
    EDOM = 33  # Math argument out of domain of func
    ERANGE = 34  # Math result not representable
    EDEADLK = 35  # Resource deadlock would occur
    ENAMETOOLONG = 36  # File name too long
    ENOLCK = 37  # No record locks available
    ENOSYS = 38  # Function not implemented
    ENOTEMPTY = 39  # Directory not empty
    ELOOP = 40  # Too many symbolic links encountered
    ENOMSG = 42  # No message of desired type
    EIDRM = 43  # Identifier removed
    ECHRNG = 44  # Channel number out of range
    EL2NSYNC = 45  # Level 2 not synchronized
    EL3HLT = 46  # Level 3 halted
    EL3RST = 47  # Level 3 reset
    ELNRNG = 48  # Link number out of range
    EUNATCH = 49  # Protocol driver not attached
    ENOCSI = 50  # No CSI structure available
    EL2HLT = 51  # Level 2 halted
    EBADE = 52  # Invalid exchange
    EBADR = 53  # Invalid request descriptor
    EXFULL = 54  # Exchange full
    ENOANO = 55  # No anode
    EBADRQC = 56  # Invalid request code
    EBADSLT = 57  # Invalid slot
    EDEADLOCK = 58  # File locking deadlock error
    EBFONT = 59  # Bad font file format
    ENOSTR = 60  # Device not a stream
    ENODATA = 61  # No data available
    ETIME = 62  # Timer expired
    ENOSR = 63  # Out of streams resources
    ENONET = 64  # Machine is not on the network
    ENOPKG = 65  # Package not installed
    EREMOTE = 66  # Object is remote
    ENOLINK = 67  # Link has been severed
    EADV = 68  # Advertise error
    ESRMNT = 69  # Srmount error
    ECOMM = 70  # Communication error on send
    EPROTO = 71  # Protocol error
    EMULTIHOP = 72  # Multihop attempted
    EDOTDOT = 73  # RFS specific error
    EBADMSG = 74  # Not a data message
    EOVERFLOW = 75  # Value too large for defined data type
    ENOTUNIQ = 76  # Name not unique on network
    EBADFD = 77  # File descriptor in bad state
    EREMCHG = 78  # Remote address changed
    ELIBACC = 79  # Can not access a needed shared library
    ELIBBAD = 80  # Accessing a corrupted shared library
    ELIBSCN = 81  # .lib section in a.out corrupted
    ELIBMAX = 82  # Attempting to link in too many shared libraries
    ELIBEXEC = 83  # Cannot exec a shared library directly
    EILSEQ = 84  # Illegal byte sequence
    ERESTART = 85  # Interrupted system call should be restarted
    ESTRPIPE = 86  # Streams pipe error
    EUSERS = 87  # Too many users
    ENOTSOCK = 88  # Socket operation on non-socket
    EDESTADDRREQ = 89  # Destination address required
    EMSGSIZE = 90  # Message too long
    EPROTOTYPE = 91  # Protocol wrong type for socket
    ENOPROTOOPT = 92  # Protocol not available
    EPROTONOSUPPORT = 93  # Protocol not supported
    ESOCKTNOSUPPORT = 94  # Socket type not supported
    EOPNOTSUPP = 95  # Operation not supported on transport endpoint
    EPFNOSUPPORT = 96  # Protocol family not supported
    EAFNOSUPPORT = 97  # Address family not supported by protocol
    EADDRINUSE = 98  # Address already in use
    EADDRNOTAVAIL = 99  # Cannot assign requested address
    ENETDOWN = 100  # Network is down
    ENETUNREACH = 101  # Network is unreachable
    ENETRESET = 102  # Network dropped connection because of reset
    ECONNABORTED = 103  # Software caused connection abort
    ECONNRESET = 104  # Connection reset by peer
    ENOBUFS = 105  # No buffer space available
    EISCONN = 106  # Transport endpoint is already connected
    ENOTCONN = 107  # Transport endpoint is not connected
    ESHUTDOWN = 108  # Cannot send after transport endpoint shutdown
    ETOOMANYREFS = 109  # Too many references: cannot splice
    ETIMEDOUT = 110  # Connection timed out
    ECONNREFUSED = 111  # Connection refused
    EHOSTDOWN = 112  # Host is down
    EHOSTUNREACH = 113  # No route to host
    EALREADY = 114  # Operation already in progress
    EINPROGRESS = 115  # Operation cde now in progress
    ESTALE = 116  # Stale NFS file handle
    EUCLEAN = 117  # Structure needs cleaning
    ENOTNAM = 118  # Not a XENIX named type file
    ENAVAIL = 119  # No XENIX semaphores available
    EISNAM = 120  # Is a named type file
    EREMOTEIO = 121  # Remote I/O error

    # Our own code errors
    EIFACE = 128  # Wrong interface selected. List of available interfaces
    EBADIP = 129  # No valid IP
    EPCIPT = 130  # No valid PCI port
    ESERPT = 131  # No valid serial port name
    ENOTAV = 132  # Not available
    EOPENDR = 133  # Error opening driver
    ECLOSDR = 134  # Error closing driver
    EBADINP = 135  # Bad input
    BADSTAT = 136  # Bad Status in WRPC

    # Dictionary for defining the code errors
    errdict = {}
    errdict[EPERM] = 'Operation not permitted'
    errdict[ENOENT] = 'No such file or directory'
    errdict[ESRCH] = 'No such process'
    errdict[EINTR] = 'Interrupted system call'
    errdict[EIO] = 'I/O error'
    errdict[ENXIO] = 'No such device or address'
    errdict[E2BIG] = 'Arg list too long'
    errdict[ENOEXEC] = 'Exec format error'
    errdict[EBADF] = 'Bad file number'
    errdict[ECHILD] = 'No child processes'
    errdict[EAGAIN] = 'Try again'
    errdict[ENOMEM] = 'Out of memory'
    errdict[EACCES] = 'Permission denied'
    errdict[EFAULT] = 'Bad address'
    errdict[ENOTBLK] = 'Block device required'
    errdict[EBUSY] = 'Device or resource busy'
    errdict[EEXIST] = 'File exists'
    errdict[EXDEV] = 'Cross-device link'
    errdict[ENODEV] = 'No such device'
    errdict[ENOTDIR] = 'Not a directory'
    errdict[EISDIR] = 'Is a directory'
    errdict[EINVAL] = 'Invalid argument'
    errdict[ENFILE] = 'File table overflow'
    errdict[EMFILE] = 'Too many open files'
    errdict[ENOTTY] = 'Not a typewriter'
    errdict[ETXTBSY] = 'Text file busy'
    errdict[EFBIG] = 'File too large'
    errdict[ENOSPC] = 'No space left on device'
    errdict[ESPIPE] = 'Illegal seek'
    errdict[EROFS] = 'Read-only file system'
    errdict[EMLINK] = 'Too many links'
    errdict[EPIPE] = 'Broken pipe'
    errdict[EDOM] = 'Math argument out of domain of func'
    errdict[ERANGE] = 'Math result not representable'
    errdict[EDEADLK] = 'Resource deadlock would occur'
    errdict[ENAMETOOLONG] = 'File name too long'
    errdict[ENOLCK] = 'No record locks available'
    errdict[ENOSYS] = 'Function not implemented'
    errdict[ENOTEMPTY] = 'Directory not empty'
    errdict[ELOOP] = 'Too many symbolic links encountered'
    errdict[ENOMSG] = 'No message of desired type'
    errdict[EIDRM] = 'Identifier removed'
    errdict[ECHRNG] = 'Channel number out of range'
    errdict[EL2NSYNC] = 'Level 2 not synchronized'
    errdict[EL3HLT] = 'Level 3 halted'
    errdict[EL3RST] = 'Level 3 reset'
    errdict[ELNRNG] = 'Link number out of range'
    errdict[EUNATCH] = 'Protocol driver not attached'
    errdict[ENOCSI] = 'No CSI structure available'
    errdict[EL2HLT] = 'Level 2 halted'
    errdict[EBADE] = 'Invalid exchange'
    errdict[EBADR] = 'Invalid request descriptor'
    errdict[EXFULL] = 'Exchange full'
    errdict[ENOANO] = 'No anode'
    errdict[EBADRQC] = 'Invalid request code'
    errdict[EBADSLT] = 'Invalid slot'
    errdict[EDEADLOCK] = 'File locking deadlock error'
    errdict[EBFONT] = 'Bad font file format'
    errdict[ENOSTR] = 'Device not a stream'
    errdict[ENODATA] = 'No data available'
    errdict[ETIME] = 'Timer expired'
    errdict[ENOSR] = 'Out of streams resources'
    errdict[ENONET] = 'Machine is not on the network'
    errdict[ENOPKG] = 'Package not installed'
    errdict[EREMOTE] = 'Object is remote'
    errdict[ENOLINK] = 'Link has been severed'
    errdict[EADV] = 'Advertise error'
    errdict[ESRMNT] = 'Srmount error'
    errdict[ECOMM] = 'Communication error on send'
    errdict[EPROTO] = 'Protocol error'
    errdict[EMULTIHOP] = 'Multihop attempted'
    errdict[EDOTDOT] = 'RFS specific error'
    errdict[EBADMSG] = 'Not a data message'
    errdict[EOVERFLOW] = 'Value too large for defined data type'
    errdict[ENOTUNIQ] = 'Name not unique on network'
    errdict[EBADFD] = 'File descriptor in bad state'
    errdict[EREMCHG] = 'Remote address changed'
    errdict[ELIBACC] = 'Can not access a needed shared library'
    errdict[ELIBBAD] = 'Accessing a corrupted shared library'
    errdict[ELIBSCN] = '.lib section in a.out corrupted'
    errdict[ELIBMAX] = 'Attempting to link in too many shared libraries'
    errdict[ELIBEXEC] = 'Cannot exec a shared library directly'
    errdict[EILSEQ] = 'Illegal byte sequence'
    errdict[ERESTART] = 'Interrupted system call should be restarted'
    errdict[ESTRPIPE] = 'Streams pipe error'
    errdict[EUSERS] = 'Too many users'
    errdict[ENOTSOCK] = 'Socket operation on non-socket'
    errdict[EDESTADDRREQ] = 'Destination address required'
    errdict[EMSGSIZE] = 'Message too long'
    errdict[EPROTOTYPE] = 'Protocol wrong type for socket'
    errdict[ENOPROTOOPT] = 'Protocol not available'
    errdict[EPROTONOSUPPORT] = 'Protocol not supported'
    errdict[ESOCKTNOSUPPORT] = 'Socket type not supported'
    errdict[EOPNOTSUPP] = 'Operation not supported on transport endpoint'
    errdict[EPFNOSUPPORT] = 'Protocol family not supported'
    errdict[EAFNOSUPPORT] = 'Address family not supported by protocol'
    errdict[EADDRINUSE] = 'Address already in use'
    errdict[EADDRNOTAVAIL] = 'Cannot assign requested address'
    errdict[ENETDOWN] = 'Network is down'
    errdict[ENETUNREACH] = 'Network is unreachable'
    errdict[ENETRESET] = 'Network dropped connection because of reset'
    errdict[ECONNABORTED] = 'Software caused connection abort'
    errdict[ECONNRESET] = 'Connection reset by peer'
    errdict[ENOBUFS] = 'No buffer space available'
    errdict[EISCONN] = 'Transport endpoint is already connected'
    errdict[ENOTCONN] = 'Transport endpoint is not connected'
    errdict[ESHUTDOWN] = 'Cannot send after transport endpoint shutdown'
    errdict[ETOOMANYREFS] = 'Too many references: cannot splice'
    errdict[ETIMEDOUT] = 'Connection timed out'
    errdict[ECONNREFUSED] = 'Connection refused'
    errdict[EHOSTDOWN] = 'Host is down'
    errdict[EHOSTUNREACH] = 'No route to host'
    errdict[EALREADY] = 'Operation already in progress'
    errdict[EINPROGRESS] = 'Operation cde now in progress'
    errdict[ESTALE] = 'Stale NFS file handle'
    errdict[EUCLEAN] = 'Structure needs cleaning'
    errdict[ENOTNAM] = 'Not a XENIX named type file'
    errdict[ENAVAIL] = 'No XENIX semaphores available'
    errdict[EISNAM] = 'Is a named type file'
    errdict[EREMOTEIO] = 'Remote I/O error'

    # Our own code errors
    errdict[EIFACE] = 'Wrong interface selected. List of available interfaces'
    errdict[EBADIP] = 'No valid IP'
    errdict[EPCIPT] = 'No valid PCI port'
    errdict[ESERPT] = 'No valid serial port name'
    errdict[ENOTAV] = 'Not available'
    errdict[EOPENDR] = 'Error opening driver'
    errdict[ECLOSDR] = 'Error closing driver'
    errdict[EBADINP] = 'Bad input'
    errdict[BADSTAT] = 'Bad status info from device\'s WRPC'


    def __init__(self) :
            '''
            Constructor

            Formats output string
            '''
