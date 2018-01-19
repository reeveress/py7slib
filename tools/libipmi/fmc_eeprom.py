#!/usr/bin/python

from ctypes import *
import array
import struct
import os

lib = cdll.LoadLibrary(os.path.dirname(__file__) + "/libipmi.so")

class c_CommonHeader(Structure):
    _fields_ = [
        ("format", c_ubyte),
        ("internal_use_off", c_ubyte),
        ("chassis_info_off", c_ubyte),
        ("board_area_off", c_ubyte),
        ("product_area_off", c_ubyte),
        ("multirecord_off", c_ubyte),
        ("pad", c_ubyte),
        ("checksum", c_ubyte)
    ]

class c_BoardInfoArea(Structure):
    _fields_ = [
        ("format", c_ubyte),
        ("area_len", c_ubyte),
        ("language", c_ubyte),
        ("mfg_date0", c_ubyte),
        ("mfg_date1", c_ubyte),
        ("mfg_date2", c_ubyte),
        ("mfgr_typelen", c_ubyte),
        ("mfgr_data", c_char_p),
        ("product_typelen", c_ubyte),
        ("product_data", c_char_p),
        ("serial_typelen", c_ubyte),
        ("serial_data", c_char_p),
        ("partnum_typelen", c_ubyte),
        ("partnum_data", c_char_p),
        ("fru_fid_typelen", c_ubyte),
        ("fru_fid_data", c_char_p),
        ("typelen_end", c_ubyte),
        ("pad_len", c_ubyte),
        ("checksum", c_ubyte)
    ]

class c_DCLoadRecord(Structure):
    _fields_ = [
        ("voltage_required", c_ubyte),
        ("nominal_voltage", c_ushort),
        ("min_voltage", c_ushort),
        ("max_voltage", c_ushort),
        ("spec_ripple", c_ushort),
        ("min_current", c_ushort),
        ("max_current", c_ushort)
    ]

class c_DCOutputRecord(Structure):
    _fields_ = [
        ("output_info", c_ubyte),
        ("nominal_voltage", c_ushort),
        ("max_neg_voltage_dev", c_ushort),
        ("max_pos_voltage_dev", c_ushort),
        ("ripple", c_ushort),
        ("min_current_draw", c_ushort),
        ("max_current_draw", c_ushort)
    ]

class c_InternalUseArea(Structure):
    _fields_ = [
        ("format", c_ubyte),
        ("len", c_int),
        ("data", c_char_p)
    ]

class InternalUseArea:
    def __init__(self, data):
        self.struct = c_InternalUseArea()
        self._as_parameter_ = byref(self.struct)
        self.struct.format = 0x1
        self.set_data(data)

    def set_data(self, data):
        self.struct.data = c_char_p(array.array('B', data).tostring())
        self.struct.len = c_int(len(data))

class CommonHeader:
    def __init__(self):
        self.struct = c_CommonHeader()
        self._as_parameter_ = byref(self.struct)
        self.struct.format = 0x1
        self.struct.chassis_info_off = 0
        self.struct.product_area_off = 0
        self.struct.pad = 0

    def set_internal_use_offset(self, off):
        self.struct.internal_use_off = off

    def set_board_info_area_offset(self, off):
        self.struct.board_area_off = off

    def set_multirecord_area_offset(self, off):
        self.multirecord_off = off

class BoardInfoArea:
    def __init__(self, date, mfgr, product, serial, partnum, fru):
        self.struct = c_BoardInfoArea()
        self._as_parameter_ = byref(self.struct)
        self.struct.format = 0x1
        self.struct.area_len = 0
        self.struct.language = 0   # English
        self.set_manufacture_date(date)
        self.set_manufacturer(mfgr)
        self.set_product_name(product)
        self.set_serial_number(serial)
        self.set_part_number(partnum)
        self.set_fru_file_id(fru)

    def set_manufacture_date(self, date):
        val = bytearray(struct.pack('>I', date))
        self.struct.mfg_date2 = c_ubyte(val[1])
        self.struct.mfg_date1 = c_ubyte(val[2])
        self.struct.mfg_date0 = c_ubyte(val[3])

    def set_manufacturer(self, data):
        self.struct.mfgr_data = c_char_p(data)
        self.struct.mfgr_typelen = (len(bytearray(data)) & 0x3f) | (0x3 << 6)

    def set_product_name(self, data):
        self.struct.product_data = c_char_p(data)
        self.struct.product_typelen = (len(bytearray(data)) & 0x3f) | (0x3 << 6)

    def set_serial_number(self, data):
        self.struct.serial_data = c_char_p(data)
        self.struct.serial_typelen = (len(bytearray(data)) & 0x3f) | (0x3 << 6)

    def set_part_number(self, data):
        self.struct.partnum_data = c_char_p(data)
        self.struct.partnum_typelen = (len(bytearray(data)) & 0x3f) | (0x3 << 6)

    def set_fru_file_id(self, data):
        self.struct.fru_fid_data = c_char_p(data)
        self.struct.fru_fid_typelen = (len(bytearray(data)) & 0x3f) | (0x3 << 6)


class DCLoadRecord:
    def __init__(self, rec_num, nom, vmin, vmax, ripple, imin, imax):
        self.struct = c_DCLoadRecord()
        self._as_parameter_ = byref(self.struct)
        self.struct.voltage_required = 0
        self.struct.nominal_voltage = 0
        self.struct.min_voltage = 0
        self.struct.max_voltage = 0
        self.struct.spec_ripple = 0
        self.struct.min_current = 0
        self.struct.max_current = 0
        self.set_record_number(rec_num)
        self.set_nominal_voltage(nom*100)
        self.set_min_voltage(vmin*100)
        self.set_max_voltage(vmax*100)
        self.set_spec_ripple(ripple*1000)
        self.set_min_current(imin)
        self.set_max_current(imax)

    def set_record_number(self, val):
        self.struct.voltage_required = int(val)

    def set_nominal_voltage(self, val):
        self.struct.nominal_voltage = int(val)

    def set_min_voltage(self, val):
        self.struct.min_voltage = int(val)

    def set_max_voltage(self, val):
        self.struct.max_voltage = int(val)

    def set_spec_ripple(self, val):
        self.struct.spec_ripple = int(val)

    def set_min_current(self, val):
        self.struct.min_current = int(val)

    def set_max_current(self, val):
        self.struct.max_current = int(val)

class DCOutputRecord:
    def __init__(self, rec_num, nom, max_neg, max_pos, ripple, imin, imax):
        self.struct = c_DCOutputRecord()
        self._as_parameter_ = byref(self.struct)
        self.struct.output_info = 0
        self.struct.nominal_voltage = 0
        self.struct.max_net_voltage_dev = 0
        self.struct.max_pos_voltage_dev = 0
        self.struct.ripple = 0
        self.struct.min_current_draw = 0
        self.struct.max_current_draw = 0
        self.set_record_number(rec_num)
        self.set_nominal_voltage(nom*100)
        self.set_max_negative_voltage_deviation(max_neg*100)
        self.set_max_positive_voltage_deviation(max_pos*100)
        self.set_ripple(ripple*1000)
        self.set_min_current_draw(imin)
        self.set_max_current_draw(imax)

    def set_record_number(self, val):
        self.struct.output_info = val

    def set_nominal_voltage(self, val):
        self.struct.nominal_voltage = int(val)

    def set_max_negative_voltage_deviation(self, val):
        self.struct.max_neg_voltage_dev = int(val)

    def set_max_positive_voltage_deviation(self, val):
        self.struct.max_pos_voltage_dev = int(val)

    def set_ripple(self, val):
        self.struct.ripple = int(val)

    def set_min_current_draw(self, val):
        self.struct.min_current_draw = int(val)

    def set_max_current_draw(self, val):
        self.struct.max_current_draw = int(val)

class c_FMCOEMData(Structure):
    _fields_ = [
        ("subtype_version", c_ubyte),
        ("other", c_ubyte),
        ("p1_a_nsig", c_ubyte),
        ("p1_b_nsig", c_ubyte),
        ("p2_a_nsig", c_ubyte),
        ("p2_b_nsig", c_ubyte),
        ("p1_p2_gbt_ntran", c_ubyte),
        ("max_clock", c_ubyte)
    ]

class c_OEMRecord(Structure):
    _fields_ = [
        ("mfg_id0", c_ubyte),
        ("mfg_id1", c_ubyte),
        ("mfg_id2", c_ubyte),
        ("data", c_FMCOEMData)
    ]


class OEMRecord:
    def __init__(self, msize, p1, p2, clockdir, pa_b1_nsig, pa_b2_nsig, pb_b1_nsig, pb_b2_nsig, pa_ngbt, pb_ngbt, maxclk):
        self.struct = c_OEMRecord()
        self._as_parameter_ = byref(self.struct)
        self.struct.data.subtype_version = 0
        self.struct.data.other = 0
        self.struct.data.p1_a_nsig = 0
        self.struct.data.p1_b_nsig = 0
        self.struct.data.p2_a_nsig = 0
        self.struct.data.p2_b_nsig = 0
        self.struct.data.p1_gbt_ntran = 0
        self.struct.data.p2_gbt_ntran = 0
        self.struct.data.max_clock = 0
        self.set_module_size(msize)
        self.set_p1_connector_size(p1)
        self.set_p2_connector_size(p2)
        self.set_clock_direction(clockdir)
        self.set_nsignals(1, 1, pa_b1_nsig)
        self.set_nsignals(1, 2, pa_b2_nsig)
        self.set_nsignals(2, 1, pb_b1_nsig)
        self.set_nsignals(2, 2, pb_b2_nsig)
        self.set_num_gbt_transceivers(1, pa_ngbt)
        self.set_num_gbt_transceivers(2, pb_ngbt)
        self.set_max_clock(maxclk)

    def set_module_size(self, val):
        self.struct.data.other &= ~(0xc0)
        self.struct.data.other |= (val << 6) & 0xc0

    def set_p1_connector_size(self, val):
        self.struct.data.other &= ~(0x30)
        self.struct.data.other |= (val << 4) & 0x30

    def set_p2_connector_size(self, val):
        self.struct.data.other &= ~(0xc)
        self.struct.data.other |= (val << 2) & 0xc

    def set_clock_direction(self, val):
        self.struct.data.other &= ~(0x2)
        self.struct.data.other |= (val << 1) & 0x2

    def set_nsignals(self, port, bank, num):
        if (port == 1):
            if (bank == 1):
                self.struct.data.p1_a_nsig = num
            elif (bank == 2):
                self.struct.data.p1_b_nsig = num
        elif (port == 2):
            if (bank == 1):
                self.struct.data.p2_a_nsig = num
            elif (bank == 2):
                self.struct.data.p2_b_nsig = num

    def set_num_gbt_transceivers(self, port, num):
        if (port == 1):
            self.struct.data.p1_p2_gbt_ntran &= ~(0xf0)
            self.struct.data.p1_p2_gbt_ntran |= (num << 4) & 0xf0
        elif (port == 2):
            self.struct.data.p1_p2_gbt_ntran &= ~(0xf)
            self.struct.data.p1_p2_gbt_ntran |= num & 0xf

    def set_max_clock(self, clock):
        self.struct.data.max_clock = clock


def ipmi_open_file(name):
    lib.ipmi_file_open(c_char_p(name))

def ipmi_close_file():
    lib.ipmi_file_close()

def ipmi_set(bia, dcload, dcout, oem, iua=None):
    lib.ipmi_set_board_info_area(bia)
    for r in dcload:
        lib.ipmi_add_dc_load_record(r)
    for r in dcout:
        lib.ipmi_add_dc_output_record(r)
    lib.ipmi_set_oem_record(oem)
    if iua != None:
        lib.ipmi_set_internal_use_area(iua)

def ipmi_write():
    lib.ipmi_write()

def ipmi_get_mfg_date(data):
    return lib.ipmi_get_mfg_date(c_char_p(data))

def ipmi_get_internal_use_data(data):
    l = c_int()
    d = c_void_p(lib.ipmi_get_internal_use_data(c_char_p(data), byref(l)))
    q = cast(d, POINTER(l.value*c_ubyte))
    return q.contents

def main():
    bia = BoardInfoArea(12345678, "CERN", "ADC100M", "1234567890", "ADC100M", "abcde")

    dcload0 = DCLoadRecord(0, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcload1 = DCLoadRecord(1, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcload2 = DCLoadRecord(2, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcload3 = DCLoadRecord(3, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcload4 = DCLoadRecord(4, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcload5 = DCLoadRecord(5, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcload = [ dcload0, dcload1, dcload2, dcload3, dcload4, dcload5 ]

    dcout0 = DCOutputRecord(0, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcout1 = DCOutputRecord(1, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcout2 = DCOutputRecord(2, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcout3 = DCOutputRecord(3, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcout4 = DCOutputRecord(4, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcout5 = DCOutputRecord(5, 2.5, 2.4, 2.6, 0.0, 0, 4000)
    dcout = [ dcout0, dcout1, dcout2, dcout3, dcout4, dcout5 ]

#    oem = OEMRecord(single width, LPC, not fitted, mezz to carrier, 68, 0, 0, 0, 0, 0, 0)
    oem = OEMRecord(0, 0, 0, 0, 68, 0, 0, 0, 0, 0, 0)

    iudata = [0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41 ]
    iua = InternalUseArea(iudata)

    # Open, set, write, close!
    ipmi_open_file("test.out")
    ipmi_set(bia, dcload, dcout, oem, iua)
    ipmi_write()
    ipmi_close_file()

    test = open('test.out', 'r').read()
    print ipmi_get_mfg_date(test)
    d = ipmi_get_internal_use_data(test)
    for v in d:
        print hex(v)

if __name__ == "__main__":
    main()

